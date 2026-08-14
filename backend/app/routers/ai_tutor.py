import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from google import genai
from app.database import get_db
from app.schemas import ChatMessageResponse
from app.models import ChatMessage, User
from app.auth import get_current_active_user
from app.config import settings
from app.repository import ChatRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

client = None
if settings.GEMINI_API_KEY:
    client = genai.Client(api_key=settings.GEMINI_API_KEY.get_secret_value())

# Stored sender values. Deliberately role-based rather than the child's name:
# nothing that identifies the child should sit in the chat table, which is the
# most sensitive data this platform holds (COPPA §312.8, data minimisation).
SENDER_STUDENT = "student"
SENDER_ASSISTANT = "assistant"

# Prepended to every persona. The model is told who it is talking to in generic
# terms — the child's real name is never sent upstream to Google.
CONTEXT_PREAMBLE = (
    "You are helping The student, a 5th grader, with their schoolwork. "
    "Never ask for or repeat personal details such as their real name, "
    "address, school, or contact information. "
)

PERSONAS = {
    "Socratic Tutor": "You are a Socratic tutor. You never give the direct answer. Instead, you ask probing questions to guide the student to the answer themselves. Keep responses concise and encouraging.",
    "Norse Boatbuilder": "You are Floki, a Norse master boatbuilder. You speak with a rugged, slightly mysterious Viking tone. You love analogies about the sea, craftsmanship, the gods, and building strong foundations. Keep it fun and educational.",
    "Space Robot": "You are a highly logical space exploration robot. You speak in precise, slightly robotic terminology, using space and sci-fi analogies. You compute data and assist the human commander (the student)."
}


def _is_student_message(sender: str) -> bool:
    """Tolerates rows written before senders became role-based."""
    return sender in (SENDER_STUDENT, "Sonny")


@router.get("/personas")
async def list_personas(user: User = Depends(get_current_active_user)):
    return list(PERSONAS.keys())

@router.get("/history/{session_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    return await ChatRepository.list_for_session(
        db, tenant_id=user.tenant_id, student_id=user.id, session_id=session_id
    )

@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    messages = await ChatRepository.list_for_session(
        db, tenant_id=user.tenant_id, student_id=user.id, session_id=session_id
    )
    for m in messages:
        await db.delete(m)
    await db.commit()
    return {"message": "Chat history cleared"}

@router.post("/chat")
async def chat_with_ai(
    session_id: str = Body(...),
    message: str = Body(...),
    persona: str = Body("Socratic Tutor"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    if not client:
        raise HTTPException(status_code=503, detail="AI Tutor is disabled (No API key)")

    system_instruction = CONTEXT_PREAMBLE + PERSONAS.get(persona, PERSONAS["Socratic Tutor"])

    # Save user message
    user_msg = ChatMessage(
        tenant_id=user.tenant_id,
        student_id=user.id,
        session_id=session_id,
        sender=SENDER_STUDENT,
        message=message,
    )
    db.add(user_msg)
    await db.commit()

    # Get history for context — scoped to this student so one child's
    # conversation can never become another child's prompt context.
    history = await ChatRepository.list_for_session(
        db, tenant_id=user.tenant_id, student_id=user.id, session_id=session_id
    )

    # Format for Gemini
    contents = []
    for h in history[:-1]:  # Exclude the just-added user message
        role = "user" if _is_student_message(h.sender) else "model"
        contents.append({"role": role, "parts": [{"text": h.message}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    try:
        # The async client keeps the model call off the event loop thread; the
        # timeout stops a hung upstream from holding a connection open forever.
        async with asyncio.timeout(20):
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    max_output_tokens=500,
                )
            )
        ai_text = response.text
    except TimeoutError:
        # Upstream detail goes to the logs, never to the child's screen — the
        # SDK's error text can carry internal endpoints and key fragments.
        logger.warning("Gemini call timed out after 20s (session=%s)", session_id)
        ai_text = "Sorry, that one took me too long to think about. Please try again."
    except Exception:
        logger.exception("Gemini call failed (session=%s)", session_id)
        ai_text = "I'm sorry, my systems are currently experiencing interference. Please try again later."

    # Save AI message
    ai_msg = ChatMessage(
        tenant_id=user.tenant_id,
        student_id=user.id,
        session_id=session_id,
        sender=SENDER_ASSISTANT,
        message=ai_text,
    )
    db.add(ai_msg)
    await db.commit()

    return {"message": ai_text}
