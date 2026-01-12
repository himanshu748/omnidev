"""
TechTrainingPro - AI Router
Endpoints for AI chat functionality
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional
import json

from app.services.openai_service import openai_service

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the AI and get a response
    
    - **message**: The user's message
    - **history**: Optional previous conversation history
    """
    history = None
    if request.history:
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    response = await openai_service.chat(request.message, history)
    return ChatResponse(response=response)


@router.websocket("/chat/stream")
async def chat_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming AI responses
    
    Send JSON: {"message": "your message", "history": [...]}
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
            
            # Stream response
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
        "model": "gpt-4o",
        "status": "configured" if openai_service.client else "not configured",
        "capabilities": ["chat", "streaming", "vision"]
    }
