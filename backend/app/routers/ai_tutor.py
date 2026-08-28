import asyncio
import logging
from datetime import date, datetime, time
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from google import genai
from app.database import get_db
from app.schemas import ChatMessageResponse
from app.models import ChatMessage, SafetyEvent, StuckFlag, User
from app.auth import get_current_active_user
from app.config import settings
from app.repository import ChatRepository
from app.services import safety

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

client = None
if settings.GEMINI_API_KEY:
    client = genai.Client(api_key=settings.GEMINI_API_KEY.get_secret_value())


# Shown to the student when the tutor is switched off. Deliberately warm and
# final rather than apologetic or error-shaped: a nine-year-old reading "503"
# or "disabled" learns that the app is broken. This says the thing is resting
# and points him back at his work.
FLOKI_RESTING_MESSAGE = (
    "Floki is having a rest at the moment. Your dad will wake him up when he's "
    "ready. Everything else still works - go and finish your quests!"
)


def floki_is_available() -> bool:
    """Both halves have to be true, and they fail for different reasons.

    FLOKI_ENABLED is the deliberate policy switch (see app/config.py for why it
    defaults to off). A missing client means the API key was never configured.
    Either one absent means no request should reach Google, so they are checked
    together everywhere rather than at each call site.
    """
    return bool(settings.FLOKI_ENABLED) and client is not None

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
    # Topic boundary. Phrased as redirection rather than refusal: a flat "I
    # can't discuss that" reads as a telling-off to a nine-year-old and teaches
    # him to stop asking, which is the opposite of what a tutor wants.
    "Stay on schoolwork and wholesome curiosity - subjects, projects, how "
    "things work, history, nature, making things. If asked about something "
    "outside that, or anything intended for adults, do not engage with it: "
    "say briefly that it is not something you help with and offer a related "
    "school topic instead. "
    "If the student seems upset, worried or unwell, do not counsel them - "
    "gently suggest they talk to their dad, and return to the work. "
    "Never suggest meeting anyone, visiting sites outside this app, or "
    "keeping anything secret from a parent."
)

PERSONAS = {
    "Socratic Tutor": "You are a Socratic tutor. You never give the direct answer. Instead, you ask probing questions to guide the student to the answer themselves. Keep responses concise and encouraging.",
    "Norse Boatbuilder": "You are Floki, a Norse master boatbuilder. You speak with a rugged, slightly mysterious Viking tone. You love analogies about the sea, craftsmanship, the gods, and building strong foundations. Keep it fun and educational.",
    "Space Robot": "You are a highly logical space exploration robot. You speak in precise, slightly robotic terminology, using space and sci-fi analogies. You compute data and assist the human commander (the student)."
}


def _is_student_message(sender: str) -> bool:
    """Tolerates rows written before senders became role-based."""
    return sender in (SENDER_STUDENT, "Sonny")


# The one tool Floki can call. Described in terms of what the student is
# experiencing rather than what the system does, because that is what the model
# has to recognise -- it never sees the parent's screen.
FLAG_STUCK_TOOL = {
    "name": "flag_stuck",
    "description": (
        "Let the student's dad know they are stuck and could use help in person. "
        "Call this when the student has tried something and it is not working, "
        "says they do not understand after an explanation, is going in circles, "
        "or is getting frustrated with a piece of schoolwork. Do not call it for "
        "an ordinary first question -- being asked something is not being stuck. "
        "Keep helping after calling it; this asks for a person as well, not instead."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": (
                    "What they are stuck on, in a few words, specific enough for "
                    "their dad to sit down and help. For example 'dividing "
                    "fractions by whole numbers' rather than 'maths'."
                ),
            }
        },
        "required": ["topic"],
    },
}

# Cap on how much the model may write into the flag; the column is 200.
TOPIC_LIMIT = 200


async def _record_stuck_flag(db: AsyncSession, user: User, session_id: str, topic: str) -> None:
    """Persist a flag, ignoring a repeat for the same topic in one session.

    Without the de-duplication a long struggle produces a flag per turn, and a
    parent opening the dashboard to eleven notices about one worksheet learns
    less than they would from one.
    """
    cleaned = (topic or "").strip()[:TOPIC_LIMIT] or "schoolwork"

    existing = await db.execute(
        select(StuckFlag).where(
            StuckFlag.tenant_id == user.tenant_id,
            StuckFlag.student_id == user.id,
            StuckFlag.session_id == session_id,
            StuckFlag.topic == cleaned,
            StuckFlag.resolved_at.is_(None),
        )
    )
    if existing.scalars().first():
        return

    db.add(StuckFlag(
        tenant_id=user.tenant_id,
        student_id=user.id,
        session_id=session_id,
        topic=cleaned,
    ))
    logger.info("Stuck flag raised (student=%s, session=%s, topic=%r)", user.id, session_id, cleaned)


def _tool_calls(response) -> list:
    """Function calls in a response, tolerating SDK shapes that lack them."""
    try:
        calls = response.function_calls
    except AttributeError:
        return []
    return list(calls or [])


async def _messages_sent_today(db: AsyncSession, user: User) -> int:
    """Count this student's own messages since local midnight."""
    since = datetime.combine(date.today(), time.min)
    result = await db.execute(
        select(func.count())
        .select_from(ChatMessage)
        .where(
            ChatMessage.tenant_id == user.tenant_id,
            ChatMessage.student_id == user.id,
            ChatMessage.sender == SENDER_STUDENT,
            ChatMessage.timestamp >= since,
        )
    )
    return result.scalar_one()


@router.get("/status")
async def floki_status(user: User = Depends(get_current_active_user)):
    """Whether the tutor is available, so the client never offers a dead box.

    The student view asks this before rendering. Without it the only way to
    discover the tutor is off is to type a question and receive an error, which
    is exactly the "crash screen for an ordinary state" the student side is not
    allowed to have.
    """
    return {"enabled": floki_is_available()}


@router.get("/personas")
async def list_personas(user: User = Depends(get_current_active_user)):
    if not floki_is_available():
        return []
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
    # Checked before the message is stored, not after: when the tutor is off,
    # nothing the child types should be persisted either. The transcript is the
    # most sensitive table here, and there is no reason to grow it while the
    # feature that reads it is switched off.
    if not floki_is_available():
        raise HTTPException(status_code=503, detail=FLOKI_RESTING_MESSAGE)

    # Cost and abuse ceiling, checked before anything is written or sent.
    if await _messages_sent_today(db, user) >= settings.FLOKI_DAILY_MESSAGE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="That's all the questions for Floki today. Ask your dad if you need more.",
        )

    system_instruction = CONTEXT_PREAMBLE + PERSONAS.get(persona, PERSONAS["Socratic Tutor"])

    # Save user message. This happens before the safety check so that a
    # disclosure is recorded even if everything after it fails -- the parent
    # needs to be able to read what was actually said.
    user_msg = ChatMessage(
        tenant_id=user.tenant_id,
        student_id=user.id,
        session_id=session_id,
        sender=SENDER_STUDENT,
        message=message,
    )
    db.add(user_msg)
    await db.commit()

    # Safety gate. A match short-circuits the model entirely: a child
    # disclosing harm should get a person, not a chatbot's best attempt at
    # counselling. The reply is fixed, the parent is alerted, and nothing is
    # sent upstream to Google.
    finding = safety.check_message(message)
    if finding:
        db.add(SafetyEvent(
            tenant_id=user.tenant_id,
            student_id=user.id,
            session_id=session_id,
            category=finding.category,
            excerpt=finding.excerpt,
        ))
        db.add(ChatMessage(
            tenant_id=user.tenant_id,
            student_id=user.id,
            session_id=session_id,
            sender=SENDER_ASSISTANT,
            message=safety.ESCALATION_REPLY,
        ))
        await db.commit()
        logger.warning(
            "Safety escalation raised (category=%s, student=%s, session=%s)",
            finding.category, user.id, session_id,
        )
        return {"message": safety.ESCALATION_REPLY, "escalated": True}

    # Get history for context — scoped to this student so one child's
    # conversation can never become another child's prompt context.
    history = await ChatRepository.list_for_session(
        db, tenant_id=user.tenant_id, student_id=user.id, session_id=session_id
    )

    # Format for Gemini. Only a trailing window of the conversation is replayed:
    # sending the whole session made the cost of each turn grow with the length
    # of the conversation, so a long afternoon cost quadratically more than a
    # short one and would eventually overrun the context window.
    previous = history[:-1]  # Exclude the just-added user message
    if settings.FLOKI_CONTEXT_MESSAGES > 0:
        previous = previous[-settings.FLOKI_CONTEXT_MESSAGES:]

    contents = []
    for h in previous:
        role = "user" if _is_student_message(h.sender) else "model"
        contents.append({"role": role, "parts": [{"text": h.message}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    config = genai.types.GenerateContentConfig(
        system_instruction=system_instruction,
        max_output_tokens=500,
        tools=[{"function_declarations": [FLAG_STUCK_TOOL]}],
    )

    flagged_topic = None

    try:
        # The async client keeps the model call off the event loop thread; the
        # timeout stops a hung upstream from holding a connection open forever.
        # The whole exchange, including a tool round trip, sits inside it.
        async with asyncio.timeout(25):
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash", contents=contents, config=config
            )

            calls = _tool_calls(response)
            if calls:
                # Record the flag, then hand the result back so the model can
                # finish its reply. Only flag_stuck is honoured -- an unknown
                # name is answered rather than executed, so a model that
                # hallucinates a tool cannot make anything happen here.
                contents.append({"role": "model", "parts": [
                    {"function_call": {"name": call.name, "args": dict(call.args or {})}}
                    for call in calls
                ]})

                results = []
                for call in calls:
                    if call.name == "flag_stuck":
                        topic = dict(call.args or {}).get("topic", "")
                        await _record_stuck_flag(db, user, session_id, topic)
                        flagged_topic = topic
                        outcome = {"ok": True, "note": "Dad has been told. Keep helping."}
                    else:
                        logger.warning("Floki requested unknown tool %r", call.name)
                        outcome = {"ok": False, "note": "No such tool."}
                    results.append({"function_response": {"name": call.name, "response": outcome}})

                contents.append({"role": "user", "parts": results})

                response = await client.aio.models.generate_content(
                    model="gemini-2.0-flash", contents=contents, config=config
                )

        ai_text = response.text
        # A turn that only called a tool can come back with no prose at all.
        if not ai_text:
            ai_text = (
                "That is a tricky one - I have let your dad know you could use a hand. "
                "Let's keep going in the meantime."
            )
    except TimeoutError:
        # Upstream detail goes to the logs, never to the child's screen — the
        # SDK's error text can carry internal endpoints and key fragments.
        logger.warning("Gemini call timed out after 25s (session=%s)", session_id)
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
    # Commits the flag alongside the reply: the two are one event, and a flag
    # without the message that caused it would leave the parent no context.
    await db.commit()

    return {"message": ai_text, "flagged_stuck": flagged_topic}
