"""Code Gen router — generate safe project files with the active AI provider and optional Context7 docs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.codegen import CodeGenRequest, CodeGenResponse, FileEntry
from app.services.ai_service import AIConfigurationError
from app.services.codegen_service import generate_project

router = APIRouter()


@router.post("/generate", response_model=CodeGenResponse)
async def codegen_generate(body: CodeGenRequest):
    """
    Generate a full project (multiple files) for the given prompt and framework.
    Uses Context7 for up-to-date docs when CONTEXT7_API_KEY is set.
    Output is validated as safe relative files before it is returned.
    """
    try:
        result = await generate_project(prompt=body.prompt, framework=body.framework)
        return CodeGenResponse(
            files=[FileEntry(path=f["path"], content=f["content"]) for f in result["files"]],
            instructions=result.get("instructions", ""),
        )
    except AIConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Code generation failed")
