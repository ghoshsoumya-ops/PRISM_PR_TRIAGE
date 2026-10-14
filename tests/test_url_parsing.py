"""Tests for GitHub URL parsing."""

import pytest
from backend.github_client import parse_pr_url


class TestParseURL:
    def test_valid_url(self):
        owner, repo, num = parse_pr_url("https://github.com/facebook/react/pull/42")
        assert owner == "facebook"
        assert repo == "react"
        assert num == 42

    def test_valid_url_trailing_slash(self):
        owner, repo, num = parse_pr_url("https://github.com/org/repo/pull/1/")
        assert owner == "org"
        assert repo == "repo"
        assert num == 1

    def test_valid_url_with_dots_and_hyphens(self):
        owner, repo, num = parse_pr_url(
            "https://github.com/my-org/my.repo-name/pull/999"
        )
        assert owner == "my-org"
        assert repo == "my.repo-name"
        assert num == 999

    def test_rejects_non_github_host(self):
        with pytest.raises(ValueError, match="Invalid GitHub"):
            parse_pr_url("https://gitlab.com/owner/repo/pull/1")

    def test_rejects_missing_pull_segment(self):
        with pytest.raises(ValueError):
            parse_pr_url("https://github.com/owner/repo/issues/1")

    def test_rejects_zero_pr_number(self):
        with pytest.raises(ValueError):
            parse_pr_url("https://github.com/owner/repo/pull/0")

    def test_rejects_negative_pr_number(self):
        with pytest.raises(ValueError):
            parse_pr_url("https://github.com/owner/repo/pull/-1")

    def test_rejects_non_numeric_pr_number(self):
        with pytest.raises(ValueError):
            parse_pr_url("https://github.com/owner/repo/pull/abc")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError):
            parse_pr_url("")

    def test_rejects_random_url(self):
        with pytest.raises(ValueError):
            parse_pr_url("https://example.com")

    def test_rejects_github_non_pr_url(self):
        with pytest.raises(ValueError):
            parse_pr_url("https://github.com/owner/repo")

    def test_strips_whitespace(self):
        owner, repo, num = parse_pr_url("  https://github.com/o/r/pull/5  ")
        assert owner == "o"
        assert repo == "r"
        assert num == 5

    def test_rejects_extra_path_segments(self):
        with pytest.raises(ValueError):
            parse_pr_url("https://github.com/owner/repo/pull/1/files")

