"""
TechTrainingPro - Gemini AI Service
Provides chat functionality powered by Google Gemini 2.0
"""

import google.generativeai as genai
from typing import AsyncGenerator, Optional, List, Dict, Any
import json

from app.config import get_settings

settings = get_settings()


class GeminiService:
    """Service for interacting with Google Gemini AI"""
    
    def __init__(self):
        self.model = None
        self.vision_model = None
        self._configure()
    
    def _configure(self):
        """Configure the Gemini API"""
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            
            # Configure main chat model
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                },
                system_instruction="""You are TechTrainingPro AI Assistant, a helpful and knowledgeable AI.
                
You help users with:
- Technical questions and coding assistance
- Cloud computing concepts (AWS, GCP, Azure)
- DevOps practices and tools
- General knowledge and research

Be concise, accurate, and friendly. Format responses with markdown when helpful.
If you don't know something, say so honestly."""
            )
            
            # Configure vision model for image analysis
            self.vision_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config={
                    "temperature": 0.4,
                    "max_output_tokens": 4096,
                }
            )
    
    async def chat(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """
        Send a message to Gemini and get a response
        
        Args:
            message: User's message
            history: Optional conversation history
            
        Returns:
            AI response text
        """
        if not self.model:
            return "⚠️ Gemini API not configured. Please add GEMINI_API_KEY to your .env file."
        
        try:
            # Build conversation history if provided
            chat_history = []
            if history:
                for msg in history:
                    role = "user" if msg.get("role") == "user" else "model"
                    chat_history.append({
                        "role": role,
                        "parts": [msg.get("content", "")]
                    })
            
            chat = self.model.start_chat(history=chat_history)
            response = await chat.send_message_async(message)
            return response.text
            
        except Exception as e:
            return f"❌ Error communicating with Gemini: {str(e)}"
    
    async def chat_stream(
        self, 
        message: str, 
        history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from Gemini
        
        Args:
            message: User's message
            history: Optional conversation history
            
        Yields:
            Chunks of the AI response
        """
        if not self.model:
            yield "⚠️ Gemini API not configured. Please add GEMINI_API_KEY to your .env file."
            return
        
        try:
            chat_history = []
            if history:
                for msg in history:
                    role = "user" if msg.get("role") == "user" else "model"
                    chat_history.append({
                        "role": role,
                        "parts": [msg.get("content", "")]
                    })
            
            chat = self.model.start_chat(history=chat_history)
            response = await chat.send_message_async(message, stream=True)
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"❌ Error: {str(e)}"
    
    async def analyze_image(
        self, 
        image_data: bytes, 
        prompt: str = "Describe this image in detail."
    ) -> str:
        """
        Analyze an image using Gemini Vision
        
        Args:
            image_data: Image bytes
            prompt: Analysis prompt
            
        Returns:
            Image analysis text
        """
        if not self.vision_model:
            return "⚠️ Gemini API not configured."
        
        try:
            import PIL.Image
            import io
            
            # Load image from bytes
            image = PIL.Image.open(io.BytesIO(image_data))
            
            # Generate response with image
            response = await self.vision_model.generate_content_async([prompt, image])
            return response.text
            
        except Exception as e:
            return f"❌ Error analyzing image: {str(e)}"


# Singleton instance
gemini_service = GeminiService()
