"""Schemas for the local model-management API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InstalledModel(BaseModel):
    name: str
    size_gb: float | None = None
    parameter_size: str = ""
    quantization: str = ""
    modified_at: str = ""


class RecommendedModel(BaseModel):
    name: str
    label: str
    size_gb: float
    roles: list[str]
    note: str
    recommended: bool


class ProviderStatus(BaseModel):
    provider: str
    text_model: str
    vision_model: str
    ollama_base_url: str | None = None
    reachable: bool
    installed: list[str] = Field(default_factory=list)
    text_model_ready: bool
    vision_model_ready: bool


class ModelsResponse(BaseModel):
    status: ProviderStatus
    installed: list[InstalledModel] = Field(default_factory=list)
    recommended: list[RecommendedModel] = Field(default_factory=list)


class PullModelRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Model reference, e.g. 'gemma4:e4b'")
