"""GitHub REST API client — fetches PR metadata and changed files."""

from __future__ import annotations

import os
import re
from typing import Tuple

import httpx

from .schemas import PullRequestInfo

_PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[a-zA-Z0-9\-_.]+)/(?P<repo>[a-zA-Z0-9\-_.]+)/pull/(?P<number>[1-9]\d*)/?$"
)

MAX_CHANGED_FILES_PAGES = 10
MAX_PATCH_CHARS = 8_000
REQUEST_TIMEOUT = 20.0


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns an error."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """Validate and parse a GitHub PR URL into (owner, repo, pr_number)."""
    url = url.strip()
    match = _PR_URL_RE.match(url)
    if not match:
        raise ValueError(
            "Invalid GitHub pull request URL. "
            "Expected format: https://github.com/OWNER/REPO/pull/NUMBER"
        )
    return match.group("owner"), match.group("repo"), int(match.group("number"))


def _build_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def fetch_pr_data(
    owner: str, repo: str, pr_number: int
) -> Tuple[PullRequestInfo, list[dict]]:
    """Fetch PR metadata and changed files from GitHub REST API."""
    headers = _build_headers()
    base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        # Fetch PR metadata
        resp = await client.get(base, headers=headers)
        if resp.status_code == 404:
            raise GitHubAPIError(
                f"Pull request not found: {owner}/{repo}#{pr_number}",
                status_code=404,
            )
        if resp.status_code == 403:
            raise GitHubAPIError(
                "GitHub API rate limit exceeded or access denied. "
                "Set GITHUB_TOKEN in .env for higher limits.",
                status_code=403,
            )
        if resp.status_code != 200:
            raise GitHubAPIError(
                f"GitHub API error: {resp.status_code}",
                status_code=502,
            )

        pr_data = resp.json()
        pr_info = PullRequestInfo(
            title=pr_data.get("title", ""),
            author=pr_data.get("user", {}).get("login", "unknown"),
            number=pr_data.get("number", pr_number),
            repo=f"{owner}/{repo}",
            base_branch=pr_data.get("base", {}).get("ref", "unknown"),
            head_branch=pr_data.get("head", {}).get("ref", "unknown"),
            state=pr_data.get("state", "unknown"),
            additions=pr_data.get("additions", 0),
            deletions=pr_data.get("deletions", 0),
            changed_files=pr_data.get("changed_files", 0),
            created_at=pr_data.get("created_at", ""),
            url=pr_data.get("html_url", ""),
        )

        # Fetch changed files with bounded pagination
        changed_files: list[dict] = []
        page = 1
        while page <= MAX_CHANGED_FILES_PAGES:
            files_resp = await client.get(
                f"{base}/files",
                headers=headers,
                params={"page": page, "per_page": 100},
            )
            if files_resp.status_code != 200:
                break

            page_files = files_resp.json()
            if not page_files:
                break

            for f in page_files:
                patch = f.get("patch", "")
                if len(patch) > MAX_PATCH_CHARS:
                    patch = patch[:MAX_PATCH_CHARS] + "\n... [patch truncated]"
                changed_files.append(
                    {
                        "filename": f.get("filename", ""),
                        "status": f.get("status", ""),
                        "additions": f.get("additions", 0),
                        "deletions": f.get("deletions", 0),
                        "changes": f.get("changes", 0),
                        "patch": patch,
                    }
                )
            page += 1

    return pr_info, changed_files

