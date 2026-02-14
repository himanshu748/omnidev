"""
Vision Lab service.
Sends images to OpenAI's vision-capable model for analysis / OCR.
"""

from __future__ import annotations

import base64

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.vision import VisionMode

_openai = AsyncOpenAI(api_key=settings.openai_api_key)

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
    Send an image to OpenAI vision and return the result.

    Args:
        image_bytes: raw file bytes
        content_type: MIME type (e.g. image/png)
        mode: analyze | ocr | custom
        custom_prompt: required when mode == "custom"
    """
    b64 = base64.b64encode(image_bytes).decode()
    data_uri = f"data:{content_type};base64,{b64}"

    if mode == VisionMode.custom:
        prompt = custom_prompt or "What do you see in this image?"
    else:
        prompt = MODE_PROMPTS[mode]

    resp = await _openai.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": data_uri, "detail": "high"},
                    },
                ],
            }
        ],
        max_tokens=2048,
    )

    choice = resp.choices[0]
    usage = resp.usage

    return {
        "mode": mode,
        "result": choice.message.content or "",
        "model": resp.model,
        "tokens_used": usage.total_tokens if usage else None,
    }
