"""Shared API error helpers for router boundaries."""

from fastapi import HTTPException


def internal_error(detail: str) -> HTTPException:
    return HTTPException(status_code=500, detail=detail)


def service_unavailable(detail: str) -> HTTPException:
    return HTTPException(status_code=503, detail=detail)


def bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=404, detail=detail)
