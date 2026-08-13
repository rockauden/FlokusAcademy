from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import google.generativeai as genai
from app.database import get_db
from app.schemas import ChatMessageCreate, ChatMessageResponse
from app.models import ChatMessage
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/ai", tags=["ai"])

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

PERSONAS = {
    "Socratic Tutor": "You are a Socratic tutor. You never give the direct answer. Instead, you ask probing questions to guide the student to the answer themselves. Keep responses concise and encouraging.",
    "Norse Boatbuilder": "You are Floki, a Norse master boatbuilder. You speak with a rugged, slightly mysterious Viking tone. You love analogies about the sea, craftsmanship, the gods, and building strong foundations. Keep it fun and educational.",
    "Space Robot": "You are a highly logical space exploration robot. You speak in precise, slightly robotic terminology, using space and sci-fi analogies. You compute data and assist the human commander (the student)."
}

@router.get("/personas")
async def list_personas(current_user: dict = Depends(get_current_user)):
    return list(PERSONAS.keys())

@router.get("/history/{session_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp))
    return result.scalars().all()

@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id))
    messages = result.scalars().all()
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
    current_user: dict = Depends(get_current_user)
):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="AI Tutor is disabled (No API key)")
        
    system_instruction = PERSONAS.get(persona, PERSONAS["Socratic Tutor"])
    
    # Save user message
    user_msg = ChatMessage(session_id=session_id, sender='Sonny', message=message)
    db.add(user_msg)
    await db.commit()
    
    # Get history for context
    result = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp))
    history = result.scalars().all()
    
    # Format for Gemini
    formatted_history = []
    for h in history[:-1]:  # Exclude the just-added user message
        role = "user" if h.sender == 'Sonny' else "model"
        formatted_history.append({"role": role, "parts": [h.message]})
        
    # Call Gemini
    try:
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(message)
        ai_text = response.text
    except Exception as e:
        ai_text = f"I'm sorry, my systems are currently experiencing interference. ({str(e)})"
        
    # Save AI message
    ai_msg = ChatMessage(session_id=session_id, sender='Floki', message=ai_text)
    db.add(ai_msg)
    await db.commit()
    
    return {"message": ai_text}
