"""API routes for PRism backend."""

from fastapi import APIRouter, HTTPException

from .schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse, HealthResponse
from .github_client import parse_pr_url, fetch_pr_data, GitHubAPIError
from .risk_analyzer import analyze_risk
from .ai_service import generate_ai_summary

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", version="1.0.0")


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def analyze_pr(request: AnalyzeRequest):
    try:
        owner, repo, pr_number = parse_pr_url(request.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        pr_meta, changed_files = await fetch_pr_data(owner, repo, pr_number)
    except GitHubAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    risk_result = analyze_risk(pr_meta, changed_files)

    ai_summary, ai_status = await generate_ai_summary(
        pr_meta, changed_files, risk_result
    )

    return AnalyzeResponse(
        pull_request=pr_meta,
        risk_score=risk_result["risk_score"],
        risk_level=risk_result["risk_level"],
        findings=risk_result["findings"],
        ai_summary=ai_summary,
        ai_status=ai_status,
        recommendations=risk_result["recommendations"],
    )

