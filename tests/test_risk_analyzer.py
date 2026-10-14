"""Tests for the deterministic risk analyzer."""

import pytest
from backend.risk_analyzer import analyze_risk
from backend.schemas import PullRequestInfo


def _make_pr(**overrides):
    defaults = dict(
        title="Test PR",
        author="testuser",
        number=1,
        repo="owner/repo",
        base_branch="main",
        head_branch="feature",
        state="open",
        additions=10,
        deletions=5,
        changed_files=2,
        created_at="2025-01-01T00:00:00Z",
        url="https://github.com/owner/repo/pull/1",
    )
    defaults.update(overrides)
    return PullRequestInfo(**defaults)


def _make_files(filenames, status="modified", additions=5, deletions=3):
    return [
        {
            "filename": fn,
            "status": status,
            "additions": additions,
            "deletions": deletions,
            "changes": additions + deletions,
            "patch": f"@@ -1,3 +1,5 @@\n+some change in {fn}",
        }
        for fn in filenames
    ]


class TestSensitiveFileDetection:
    def test_env_file(self):
        result = analyze_risk(_make_pr(), _make_files([".env.production"]))
        categories = [f.category for f in result["findings"]]
        assert "security" in categories

    def test_private_key(self):
        result = analyze_risk(_make_pr(), _make_files(["server.pem"]))
        assert any(f.severity == "high" for f in result["findings"])

    def test_workflow_file(self):
        result = analyze_risk(
            _make_pr(), _make_files([".github/workflows/ci.yml"])
        )
        categories = [f.category for f in result["findings"]]
        assert "cicd" in categories

    def test_package_json(self):
        result = analyze_risk(_make_pr(), _make_files(["package.json"]))
        categories = [f.category for f in result["findings"]]
        assert "dependency" in categories

    def test_lockfile(self):
        result = analyze_risk(_make_pr(), _make_files(["package-lock.json"]))
        categories = [f.category for f in result["findings"]]
        assert "dependency" in categories

    def test_codeowners(self):
        result = analyze_risk(_make_pr(), _make_files(["CODEOWNERS"]))
        categories = [f.category for f in result["findings"]]
        assert "permission" in categories

    def test_no_sensitive_files(self):
        result = analyze_risk(_make_pr(), _make_files(["src/app.js"]))
        assert len(result["findings"]) == 0


class TestChangeSizeDetection:
    def test_large_change(self):
        pr = _make_pr(additions=2000, deletions=500, changed_files=20)
        result = analyze_risk(pr, _make_files(["a.js"]))
        categories = [f.category for f in result["findings"]]
        assert "size" in categories

    def test_very_large_change(self):
        pr = _make_pr(additions=5000, deletions=1000, changed_files=10)
        result = analyze_risk(pr, _make_files(["a.js"]))
        size_findings = [f for f in result["findings"] if f.category == "size"]
        assert any(f.severity == "high" for f in size_findings)

    def test_many_files(self):
        pr = _make_pr(changed_files=60)
        result = analyze_risk(pr, _make_files(["a.js"]))
        assert any("files" in f.title.lower() for f in result["findings"])

    def test_small_change_no_size_finding(self):
        pr = _make_pr(additions=10, deletions=5, changed_files=2)
        result = analyze_risk(pr, _make_files(["a.js"]))
        categories = [f.category for f in result["findings"]]
        assert "size" not in categories


class TestEmptyDiff:
    def test_no_files(self):
        result = analyze_risk(_make_pr(), [])
        assert any(f.category == "evidence" for f in result["findings"])

    def test_many_empty_patches(self):
        files = [
            {"filename": f"file{i}.bin", "status": "modified", "additions": 0,
             "deletions": 0, "changes": 0, "patch": ""}
            for i in range(6)
        ]
        result = analyze_risk(_make_pr(changed_files=6), files)
        assert any(f.category == "evidence" for f in result["findings"])


class TestBinaryFiles:
    def test_exe_file(self):
        result = analyze_risk(_make_pr(), _make_files(["malware.exe"]))
        assert any(
            f.category == "security" and "binary" in f.title.lower()
            for f in result["findings"]
        )

    def test_dll_file(self):
        result = analyze_risk(_make_pr(), _make_files(["library.dll"]))
        assert any("binary" in f.title.lower() for f in result["findings"])


class TestScoring:
    def test_score_range(self):
        pr = _make_pr(additions=5000, deletions=2000, changed_files=100)
        files = _make_files(
            [".env", ".github/workflows/deploy.yml", "package.json", "auth.py"]
        )
        result = analyze_risk(pr, files)
        assert 0 <= result["risk_score"] <= 100

    def test_low_risk(self):
        result = analyze_risk(_make_pr(), _make_files(["readme.md"]))
        assert result["risk_level"] == "low"

    def test_risk_levels_valid(self):
        pr = _make_pr(additions=5000, deletions=2000)
        result = analyze_risk(pr, _make_files([".env", "secret.key"]))
        assert result["risk_level"] in ("low", "medium", "high", "critical")


class TestRecommendations:
    def test_has_recommendations(self):
        result = analyze_risk(_make_pr(), _make_files(["readme.md"]))
        assert len(result["recommendations"]) > 0

    def test_security_recommendation(self):
        result = analyze_risk(_make_pr(), _make_files([".env"]))
        assert any("security" in r.lower() or "sensitive" in r.lower()
                    for r in result["recommendations"])

