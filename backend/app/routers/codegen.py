"""Code Gen router — generate apps with optional Context7 docs and Vercel Sandbox instructions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.codegen import CodeGenRequest, CodeGenResponse, FileEntry
from app.services.codegen_service import generate_project

router = APIRouter()


@router.post("/generate", response_model=CodeGenResponse)
async def codegen_generate(body: CodeGenRequest):
    """
    Generate a full project (multiple files) for the given prompt and framework.
    Uses optional Context7 docs when CONTEXT7_API_KEY is set.
    Output can be run locally or optionally in Vercel Sandbox (see response instructions).
    """
    try:
        result = await generate_project(prompt=body.prompt, framework=body.framework)
        return CodeGenResponse(
            files=[FileEntry(path=f["path"], content=f["content"]) for f in result["files"]],
            instructions=result.get("instructions", ""),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
