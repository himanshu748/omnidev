from fastapi import APIRouter, Request

from app.services.auth_service import generate_api_key

router = APIRouter()


@router.get("/me")
async def get_me(request: Request):
    return {
        "user_id": request.state.user_id,
        "role": request.state.user_role,
    }


@router.post("/api-key")
async def create_api_key(request: Request):
    api_key = generate_api_key(request.state.user_id)
    return {"api_key": api_key}
