"""
Vision Lab service.
Sends images to the active AI provider (Gemini cloud or Ollama local) for analysis / OCR.
"""

from __future__ import annotations

from app.services.ai_service import analyze_image_bytes
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
    Send an image to the active AI provider and return the result.
    """
    if mode == VisionMode.custom:
        prompt = custom_prompt or "What do you see in this image?"
    else:
        prompt = MODE_PROMPTS[mode]

    result = await analyze_image_bytes(prompt, image_bytes, content_type, max_tokens=2048)
    return {"mode": mode, **result}
