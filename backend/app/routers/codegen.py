"""Code Gen router — generate safe project files with the active AI provider and optional Context7 docs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.codegen import (
    CodeGenRefineRequest,
    CodeGenRequest,
    CodeGenResponse,
    FileEntry,
)
from app.services.ai_service import AIConfigurationError
from app.services.codegen_service import generate_project, refine_project

router = APIRouter()


def _to_response(result: dict) -> CodeGenResponse:
    return CodeGenResponse(
        files=[FileEntry(path=f["path"], content=f["content"]) for f in result["files"]],
        instructions=result.get("instructions", ""),
        summary=result.get("summary", ""),
        entry=result.get("entry", ""),
    )


@router.post("/generate", response_model=CodeGenResponse)
async def codegen_generate(body: CodeGenRequest):
    """
    Generate a full project (multiple files) for the given prompt and framework.
    Uses Context7 for up-to-date docs when CONTEXT7_API_KEY is set.
    Output is validated as safe relative files before it is returned.
    """
    try:
        result = await generate_project(prompt=body.prompt, framework=body.framework)
        return _to_response(result)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Code generation failed")


@router.post("/refine", response_model=CodeGenResponse)
async def codegen_refine(body: CodeGenRefineRequest):
    """
    Iterate on an existing generated project: apply a natural-language instruction
    and return the modified file set. Runs the same path/secret/npm validation as
    generation on both the incoming files and the model output.
    """
    try:
        result = await refine_project(
            files=[{"path": f.path, "content": f.content} for f in body.files],
            instruction=body.instruction,
            framework=body.framework,
        )
        return _to_response(result)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Code generation failed")
