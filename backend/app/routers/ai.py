"""
OmniDev - AI Router
Endpoints for AI chat functionality with user-configurable API keys
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional
from openai import AsyncOpenAI
import json

from app.services.openai_service import openai_service
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None
    api_key: Optional[str] = None  # User-provided API key


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


def get_system_prompt() -> str:
    """Get the system prompt for the AI assistant"""
    return """You are OmniDev AI Assistant, a powerful and knowledgeable AI powered by OpenAI GPT-5 Nano.
    
You help users with:
- Technical questions and coding assistance
- Cloud computing concepts (AWS, GCP, Azure)
- DevOps practices and tools
- Web scraping and browser automation
- General knowledge and research
- Image analysis and vision tasks

Be concise, accurate, and friendly. Format responses with markdown when helpful.
If you don't know something, say so honestly."""


async def chat_with_key(message: str, history: Optional[List[dict]], api_key: str) -> str:
    """Chat using a user-provided API key"""
    try:
        client = AsyncOpenAI(api_key=api_key)
        messages = [{"role": "system", "content": get_system_prompt()}]
        
        if history:
            for msg in history:
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
        response = await client.chat.completions.create(
            model="gpt-5-nano-2025-08-07",
            messages=messages,
            temperature=0.7,
            max_tokens=8192,
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error with your API key: {str(e)}"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the AI and get a response
    
    - **message**: The user's message
    - **history**: Optional previous conversation history
    - **api_key**: Optional user-provided OpenAI API key
    """
    history = None
    if request.history:
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    # Use user-provided key if available
    if request.api_key:
        response = await chat_with_key(request.message, history, request.api_key)
    else:
        response = await openai_service.chat(request.message, history)
    
    return ChatResponse(response=response)


@router.websocket("/chat/stream")
async def chat_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming AI responses
    
    Send JSON: {"message": "your message", "history": [...], "api_key": "optional"}
    Receive chunked text responses
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            message = request_data.get("message", "")
            history = request_data.get("history", [])
            api_key = request_data.get("api_key")
            
            # Use user key or fallback to service
            if api_key:
                client = AsyncOpenAI(api_key=api_key)
                messages = [{"role": "system", "content": get_system_prompt()}]
                for msg in history:
                    messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
                messages.append({"role": "user", "content": message})
                
                stream = await client.chat.completions.create(
                    model="gpt-5-nano-2025-08-07",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=8192,
                    stream=True,
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        await websocket.send_text(json.dumps({
                            "type": "chunk",
                            "content": chunk.choices[0].delta.content
                        }))
            else:
                async for chunk in openai_service.chat_stream(message, history):
                    await websocket.send_text(json.dumps({
                        "type": "chunk",
                        "content": chunk
                    }))
            
            # Send completion signal
            await websocket.send_text(json.dumps({
                "type": "done"
            }))
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": str(e)
        }))


@router.get("/status")
async def ai_status():
    """Check AI service status"""
    return {
        "service": "OpenAI",
        "model": "gpt-5-nano-2025-08-07",
        "status": "configured" if openai_service.client else "not configured",
        "capabilities": ["chat", "streaming", "vision", "user-api-key"]
    }
