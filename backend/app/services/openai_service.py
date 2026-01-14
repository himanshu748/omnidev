"""
OmniDev - OpenAI AI Service
Provides chat functionality powered by OpenAI GPT-5 Nano
"""

from openai import AsyncOpenAI
from typing import AsyncGenerator, Optional, List, Dict
import base64

from app.config import get_settings

settings = get_settings()


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.client = None
        self.model = "gpt-5-nano-2025-08-07"  # Latest efficient model
        self.vision_model = "gpt-5-nano-2025-08-07"  # GPT-5 Nano has built-in vision
        self.reasoning_model = "gpt-5-nano-2025-08-07"  # For complex reasoning tasks
        self._configure()
    
    def _configure(self):
        """Configure the OpenAI API"""
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    def _get_system_prompt(self) -> str:
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

    async def chat(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """
        Send a message to OpenAI and get a response
        
        Args:
            message: User's message
            history: Optional conversation history
            
        Returns:
            AI response text
        """
        if not self.client:
            return "⚠️ OpenAI API not configured. Please add OPENAI_API_KEY to your .env file."
        
        try:
            # Build messages list
            messages = [{"role": "system", "content": self._get_system_prompt()}]
            
            # Add conversation history if provided
            if history:
                for msg in history:
                    role = "user" if msg.get("role") == "user" else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg.get("content", "")
                    })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Get response from OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=8192,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error communicating with OpenAI: {str(e)}"
    
    async def chat_stream(
        self, 
        message: str, 
        history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from OpenAI
        
        Args:
            message: User's message
            history: Optional conversation history
            
        Yields:
            Chunks of the AI response
        """
        if not self.client:
            yield "⚠️ OpenAI API not configured. Please add OPENAI_API_KEY to your .env file."
            return
        
        try:
            messages = [{"role": "system", "content": self._get_system_prompt()}]
            
            if history:
                for msg in history:
                    role = "user" if msg.get("role") == "user" else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg.get("content", "")
                    })
            
            messages.append({"role": "user", "content": message})
            
            # Stream response from OpenAI
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=8192,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"❌ Error: {str(e)}"
    
    async def analyze_image(
        self, 
        image_data: bytes, 
        prompt: str = "Describe this image in detail."
    ) -> str:
        """
        Analyze an image using OpenAI GPT-4o Vision
        
        Args:
            image_data: Image bytes
            prompt: Analysis prompt
            
        Returns:
            Image analysis text
        """
        if not self.client:
            return "⚠️ OpenAI API not configured."
        
        try:
            # Convert image bytes to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Determine image type (assume jpeg if unknown)
            # You could add proper detection here
            media_type = "image/jpeg"
            
            # Create message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                max_tokens=4096,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error analyzing image: {str(e)}"


# Singleton instance
openai_service = OpenAIService()
