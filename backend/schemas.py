"""Pydantic schemas for API request/response contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="GitHub pull request URL")


class PullRequestInfo(BaseModel):
    title: str
    author: str
    number: int
    repo: str
    base_branch: str
    head_branch: str
    state: str
    additions: int
    deletions: int
    changed_files: int
    created_at: str
    url: str


class Finding(BaseModel):
    category: str
    severity: str = Field(..., description="low, medium, high, or critical")
    title: str
    description: str
    file: str | None = None


class AnalyzeResponse(BaseModel):
    pull_request: PullRequestInfo
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str = Field(..., description="low, medium, high, or critical")
    findings: list[Finding]
    ai_summary: str | None = None
    ai_status: str = Field(
        default="unavailable",
        description="available, unavailable, error, or disabled",
    )
    recommendations: list[str]


class HealthResponse(BaseModel):
    status: str
    version: str


class ErrorResponse(BaseModel):
    detail: str

