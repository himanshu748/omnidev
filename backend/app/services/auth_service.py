import base64
import hashlib
import hmac
from typing import Dict, Any

from jose import jwt, JWTError
from fastapi import HTTPException, status

from app.config import get_settings


settings = get_settings()


def decode_jwt(token: str) -> Dict[str, Any]:
    if not settings.supabase_jwt_secret:
        raise HTTPException(status_code=503, detail="Supabase JWT secret not configured")
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_user_id(payload: Dict[str, Any]) -> str:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user_id


def generate_api_key(user_id: str) -> str:
    digest = hmac.new(
        settings.api_key_salt.encode("utf-8"),
        user_id.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def verify_api_key(user_id: str, api_key: str) -> bool:
    expected = generate_api_key(user_id)
    return hmac.compare_digest(expected, api_key)
