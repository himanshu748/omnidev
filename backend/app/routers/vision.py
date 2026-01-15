"""
OmniDev - Vision Router
Endpoints for image analysis and vision features using OpenAI GPT-5 Mini Vision
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.openai_service import openai_service

router = APIRouter()


class AnalysisResponse(BaseModel):
    analysis: str
    status: str = "success"


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form("Describe this image in detail. Include objects, colors, setting, and any text visible.")
):
    """
    Analyze an uploaded image using OpenAI GPT-5 Mini Vision
    
    - **file**: Image file (JPEG, PNG, WebP)
    - **prompt**: Custom analysis prompt (optional)
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Read file content
    image_data = await file.read()
    
    # Analyze with OpenAI
    result = await openai_service.analyze_image(image_data, prompt)
    
    return AnalysisResponse(analysis=result)


@router.post("/describe")
async def describe_image(file: UploadFile = File(...)):
    """Get a detailed description of an image"""
    image_data = await file.read()
    result = await openai_service.analyze_image(
        image_data, 
        "Provide a comprehensive description of this image including:\n"
        "1. Main subjects and objects\n"
        "2. Colors and visual style\n"
        "3. Setting and context\n"
        "4. Any text visible\n"
        "5. Overall mood or tone"
    )
    return {"description": result}


@router.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    """Extract text (OCR) from an image"""
    image_data = await file.read()
    result = await openai_service.analyze_image(
        image_data,
        "Extract and transcribe ALL text visible in this image. "
        "Format the text clearly, preserving structure where possible. "
        "If no text is visible, say 'No text detected'."
    )
    return {"text": result}


@router.post("/identify-objects")
async def identify_objects(file: UploadFile = File(...)):
    """Identify and list objects in an image"""
    image_data = await file.read()
    result = await openai_service.analyze_image(
        image_data,
        "Identify all objects in this image. Return as a JSON-formatted list with:\n"
        "- object: name of the object\n"
        "- confidence: high/medium/low\n"
        "- location: general position (top-left, center, etc.)"
    )
    return {"objects": result}


@router.get("/status")
async def vision_status():
    """Check Vision service status"""
    return {
        "service": "OpenAI Vision",
        "model": "gpt-5-mini",
        "status": "configured" if openai_service.client else "not configured",
        "capabilities": ["image-analysis", "ocr", "object-detection", "custom-prompts"]
    }
