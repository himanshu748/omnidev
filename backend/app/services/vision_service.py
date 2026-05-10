"""
Vision Lab service.

Sends images to the configured optional AI provider for analysis / OCR.
Google Gemini is the current provider implementation.
"""

from __future__ import annotations

from google.genai import types

from app.config import settings
from app.services.ai_service import get_client, get_response_text, total_tokens_used
from app.schemas.vision import VisionMode

MODE_PROMPTS = {
    VisionMode.analyze: (
        "Describe this image in detail. Include objects, colours, text, layout, "
        "and any notable features."
    ),
    VisionMode.ocr: (
        "Extract ALL text visible in this image. Return the raw text only, "
        "preserving the original layout as closely as possible."
    ),
}


async def analyze_image(
    image_bytes: bytes,
    content_type: str,
    mode: VisionMode = VisionMode.analyze,
    custom_prompt: str | None = None,
) -> dict:
    """
    Send an image to the configured AI provider and return the result.
    """
    if mode == VisionMode.custom:
        prompt = custom_prompt or "What do you see in this image?"
    else:
        prompt = MODE_PROMPTS[mode]

    client = get_client()
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=content_type)

    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=[prompt, image_part],
        config=types.GenerateContentConfig(max_output_tokens=2048),
    )

    return {
        "mode": mode,
        "result": get_response_text(resp),
        "model": settings.gemini_model,
        "tokens_used": total_tokens_used(resp),
    }
