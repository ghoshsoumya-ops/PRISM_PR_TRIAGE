"""Tests for the FastAPI routes using the test client."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.schemas import PullRequestInfo
from backend.github_client import GitHubAPIError


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestAnalyzeEndpoint:
    def test_rejects_invalid_url(self):
        resp = client.post("/api/analyze", json={"url": "not-a-url"})
        assert resp.status_code == 400

    def test_rejects_missing_url(self):
        resp = client.post("/api/analyze", json={})
        assert resp.status_code == 422

    def test_rejects_non_github_url(self):
        resp = client.post(
            "/api/analyze",
            json={"url": "https://gitlab.com/o/r/pull/1"},
        )
        assert resp.status_code == 400

    @patch("backend.routes.fetch_pr_data", new_callable=AsyncMock)
    @patch("backend.routes.generate_ai_summary", new_callable=AsyncMock)
    def test_successful_analysis(self, mock_ai, mock_fetch):
        mock_fetch.return_value = (
            PullRequestInfo(
                title="Test PR",
                author="user",
                number=1,
                repo="owner/repo",
                base_branch="main",
                head_branch="feat",
                state="open",
                additions=10,
                deletions=5,
                changed_files=2,
                created_at="2025-01-01T00:00:00Z",
                url="https://github.com/owner/repo/pull/1",
            ),
            [
                {
                    "filename": "readme.md",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 5,
                    "changes": 15,
                    "patch": "+hello",
                }
            ],
        )
        mock_ai.return_value = (None, "unavailable")

        resp = client.post(
            "/api/analyze",
            json={"url": "https://github.com/owner/repo/pull/1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_score" in data
        assert "risk_level" in data
        assert "findings" in data
        assert "recommendations" in data
        assert "pull_request" in data
        assert data["pull_request"]["title"] == "Test PR"

    @patch("backend.routes.fetch_pr_data", new_callable=AsyncMock)
    def test_github_api_error(self, mock_fetch):
        mock_fetch.side_effect = GitHubAPIError("Not found", status_code=404)
        resp = client.post(
            "/api/analyze",
            json={"url": "https://github.com/owner/repo/pull/999"},
        )
        assert resp.status_code == 404

    @patch("backend.routes.fetch_pr_data", new_callable=AsyncMock)
    def test_github_rate_limit(self, mock_fetch):
        mock_fetch.side_effect = GitHubAPIError("Rate limited", status_code=403)
        resp = client.post(
            "/api/analyze",
            json={"url": "https://github.com/owner/repo/pull/1"},
        )
        assert resp.status_code == 403


class TestResponseSchema:
    @patch("backend.routes.fetch_pr_data", new_callable=AsyncMock)
    @patch("backend.routes.generate_ai_summary", new_callable=AsyncMock)
    def test_response_matches_schema(self, mock_ai, mock_fetch):
        mock_fetch.return_value = (
            PullRequestInfo(
                title="Schema Test",
                author="user",
                number=5,
                repo="o/r",
                base_branch="main",
                head_branch="dev",
                state="open",
                additions=100,
                deletions=50,
                changed_files=5,
                created_at="2025-01-01T00:00:00Z",
                url="https://github.com/o/r/pull/5",
            ),
            [
                {
                    "filename": ".env.local",
                    "status": "added",
                    "additions": 10,
                    "deletions": 0,
                    "changes": 10,
                    "patch": "+SECRET=xxx",
                }
            ],
        )
        mock_ai.return_value = ("AI insight here", "available")

        resp = client.post(
            "/api/analyze",
            json={"url": "https://github.com/o/r/pull/5"},
        )
        assert resp.status_code == 200
        data = resp.json()

        # Verify all required fields exist
        assert isinstance(data["risk_score"], int)
        assert 0 <= data["risk_score"] <= 100
        assert data["risk_level"] in ("low", "medium", "high", "critical")
        assert isinstance(data["findings"], list)
        assert isinstance(data["recommendations"], list)
        assert data["ai_summary"] == "AI insight here"
        assert data["ai_status"] == "available"

        # Verify finding structure
        if data["findings"]:
            f = data["findings"][0]
            assert "category" in f
            assert "severity" in f
            assert "title" in f
            assert "description" in f

