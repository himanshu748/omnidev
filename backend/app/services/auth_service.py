import base64
import hashlib
import hmac
import time
from typing import Dict, Any, Optional, List

import httpx
from jose import jwk, jwt, JWTError
from fastapi import HTTPException, status

from app.config import get_settings


settings = get_settings()

_JWKS_CACHE: dict[str, Any] = {"fetched_at": 0.0, "keys": []}
_JWKS_TTL_SECONDS = 60 * 10  # 10 minutes


def _fetch_jwks_keys() -> List[Dict[str, Any]]:
    if not settings.supabase_jwks_url:
        return []
    try:
        resp = httpx.get(settings.supabase_jwks_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        keys = data.get("keys", [])
        return keys if isinstance(keys, list) else []
    except Exception:
        return []


def _get_jwk_for_kid(kid: Optional[str]) -> Optional[Dict[str, Any]]:
    if not kid:
        return None

    now = time.time()
    stale = (now - float(_JWKS_CACHE.get("fetched_at", 0.0))) > _JWKS_TTL_SECONDS
    if stale or not _JWKS_CACHE.get("keys"):
        _JWKS_CACHE["keys"] = _fetch_jwks_keys()
        _JWKS_CACHE["fetched_at"] = now

    keys: List[Dict[str, Any]] = _JWKS_CACHE.get("keys", []) or []
    for k in keys:
        if k.get("kid") == kid:
            return k

    # Refresh once more (rotation)
    _JWKS_CACHE["keys"] = _fetch_jwks_keys()
    _JWKS_CACHE["fetched_at"] = now
    keys = _JWKS_CACHE.get("keys", []) or []
    for k in keys:
        if k.get("kid") == kid:
            return k
    return None


def decode_jwt(token: str) -> Dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    alg = header.get("alg")
    kid = header.get("kid")
    options = {"verify_aud": False}
    issuer = settings.supabase_jwt_issuer or None

    # Legacy shared-secret tokens (HS256)
    if alg == "HS256":
        if not settings.supabase_jwt_secret:
            raise HTTPException(
                status_code=503,
                detail="Supabase JWT secret not configured (set SUPABASE_JWT_SECRET or SUPABASE_JWKS_URL)",
            )
        try:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options=options,
                issuer=issuer,
            )
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Modern Supabase projects use asymmetric signing (often ES256) exposed via JWKS.
    if not settings.supabase_jwks_url:
        raise HTTPException(status_code=503, detail="Supabase JWKS URL not configured (set SUPABASE_JWKS_URL)")

    jwk_data = _get_jwk_for_kid(kid)
    if not jwk_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        key = jwk.construct(jwk_data)
        pem = key.to_pem()
        if isinstance(pem, bytes):
            pem = pem.decode("utf-8")
        return jwt.decode(
            token,
            pem,
            algorithms=[alg] if alg else None,
            options=options,
            issuer=issuer,
        )
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
