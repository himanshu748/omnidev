"""Vision Lab router — image analysis & OCR via Gemini."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.vision import VisionMode, VisionResponse
from app.services.vision_service import analyze_image
from app.routers.errors import internal_error, service_unavailable

router = APIRouter()

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


@router.post("/analyze", response_model=VisionResponse)
async def vision_analyze(
    image: UploadFile = File(...),
    mode: VisionMode = Form(VisionMode.analyze),
    prompt: str = Form(""),
):
    """
    Upload an image for AI analysis.

    Modes:
    - **analyze** — general image description
    - **ocr** — extract text from the image
    - **custom** — use your own prompt
    """
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image.content_type}. "
            f"Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")

    try:
        result = await analyze_image(
            image_bytes=image_bytes,
            content_type=image.content_type or "image/png",
            mode=mode,
            custom_prompt=prompt if mode == VisionMode.custom else None,
        )
        return VisionResponse(**result)
    except ValueError as exc:
        if "GEMINI_API_KEY" in str(exc):
            raise service_unavailable(str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise internal_error("Vision analysis failed.") from exc
