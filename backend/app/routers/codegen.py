"""Code Gen router — generate websites/apps with Context7 docs; run in Vercel Sandbox."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.codegen import CodeGenRequest, CodeGenResponse, FileEntry
from app.services.codegen_service import generate_project, generate_background_image

router = APIRouter()


@router.post("/generate-image")
async def codegen_generate_image(body: dict):
    """
    Generate a hero/background image when needed (e.g. for landing pages).
    Returns base64 PNG. Uses OpenAI DALL-E.
    """
    prompt = body.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt required")
    try:
        b64 = await generate_background_image(prompt)
        return {"image_b64": b64}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate", response_model=CodeGenResponse)
async def codegen_generate(body: CodeGenRequest):
    """
    Generate a full project (multiple files) for the given prompt and framework.
    Uses Context7 for up-to-date docs when CONTEXT7_API_KEY is set.
    Output is ready to run in Vercel Sandbox (see instructions in response).
    """
    try:
        result = await generate_project(prompt=body.prompt, framework=body.framework)
        return CodeGenResponse(
            files=[FileEntry(path=f["path"], content=f["content"]) for f in result["files"]],
            instructions=result.get("instructions", ""),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
