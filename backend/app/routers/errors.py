"""Shared API error helpers for router boundaries."""

from fastapi import HTTPException


def internal_error(detail: str) -> HTTPException:
    return HTTPException(status_code=500, detail=detail)
