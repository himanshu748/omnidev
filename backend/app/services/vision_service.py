"""
Vision Lab service.
Sends images to Claude for analysis / OCR.
"""

from __future__ import annotations

import base64

from app.config import settings
from app.schemas.vision import VisionMode
from app.services.anthropic_service import extract_text_from_message, get_claude_client, total_tokens_used

_claude = get_claude_client()

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
    Send an image to Claude and return the result.

    Args:
        image_bytes: raw file bytes
        content_type: MIME type (e.g. image/png)
        mode: analyze | ocr | custom
        custom_prompt: required when mode == "custom"
    """
    b64 = base64.b64encode(image_bytes).decode()
    if mode == VisionMode.custom:
        prompt = custom_prompt or "What do you see in this image?"
    else:
        prompt = MODE_PROMPTS[mode]

    resp = await _claude.messages.create(
        model=settings.anthropic_model,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": content_type,
                            "data": b64,
                        },
                    },
                ],
            }
        ],
    )

    return {
        "mode": mode,
        "result": extract_text_from_message(resp),
        "model": resp.model,
        "tokens_used": total_tokens_used(resp),
    }
