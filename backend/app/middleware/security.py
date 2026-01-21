import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import get_settings
from app.services.auth_service import decode_jwt, get_user_id, verify_api_key
from app.services.metrics import record


settings = get_settings()


class RateLimiter:
    def __init__(self):
        self.events: Dict[str, Deque[float]] = defaultdict(deque)
        self.blocks: Dict[str, float] = {}

    def _cleanup(self, key: str, window: float) -> None:
        now = time.time()
        while self.events[key] and self.events[key][0] <= now - window:
            self.events[key].popleft()

    def allow(self, key: str, limit: int, window: float, block_seconds: int) -> None:
        now = time.time()
        blocked_until = self.blocks.get(key)
        if blocked_until and blocked_until > now:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        self._cleanup(key, window)
        if len(self.events[key]) >= limit:
            self.blocks[key] = now + block_seconds
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        self.events[key].append(now)


rate_limiter = RateLimiter()


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if request.scope.get("type") != "http":
            return await call_next(request)

        if path in {"/", "/health"} or path.startswith(("/docs", "/redoc", "/openapi.json")):
            return await call_next(request)

        if path.startswith("/analytics"):
            return await call_next(request)

        if not path.startswith("/api/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Authorization required"})

        try:
            payload = decode_jwt(token)
            user_id = get_user_id(payload)
            request.state.user_id = user_id
            request.state.user_role = payload.get("role")
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        if not path.startswith("/api/auth/"):
            api_key = request.headers.get("X-API-Key", "")
            if not api_key or not verify_api_key(user_id, api_key):
                return JSONResponse(status_code=403, content={"detail": "Invalid API key"})

        key = f"{user_id}:{path}"
        try:
            rate_limiter.allow(
                key,
                limit=settings.rate_limit_per_minute,
                window=60,
                block_seconds=settings.rate_limit_block_seconds,
            )
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        response = await call_next(request)
        record(path, response.status_code)
        return response
