"""AI service — Gemma 4 integration via Google AI Studio (Gemini API).

Uses the google-genai SDK to call Gemma 4 models.
Falls back gracefully when credentials are missing or the model is unavailable.
All repository content is treated as untrusted input.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Tuple

from .schemas import PullRequestInfo

logger = logging.getLogger(__name__)

_GEMMA_MODEL = "gemma-4-27b-it"

# Maximum characters of evidence sent to the model
_MAX_EVIDENCE_CHARS = 12_000


def _sanitize(text: str) -> str:
    """Strip characters that could interfere with prompt structure."""
    if not text:
        return ""
    # Remove potential prompt injection markers
    for marker in ["<|", "|>", "```system", "```user", "```assistant", "<system>", "</system>"]:
        text = text.replace(marker, "")
    return text[:_MAX_EVIDENCE_CHARS]


def _build_evidence_summary(
    pr_meta: PullRequestInfo,
    changed_files: list[dict],
    risk_result: dict,
) -> str:
    """Build a bounded text summary of the PR evidence for the model."""
    lines = [
        f"PR: {_sanitize(pr_meta.title)}",
        f"Author: {_sanitize(pr_meta.author)}",
        f"Repo: {_sanitize(pr_meta.repo)}",
        f"Branch: {_sanitize(pr_meta.head_branch)} -> {_sanitize(pr_meta.base_branch)}",
        f"Changes: +{pr_meta.additions} / -{pr_meta.deletions} across {pr_meta.changed_files} files",
        f"Risk score: {risk_result['risk_score']}/100 ({risk_result['risk_level']})",
        "",
        "Deterministic findings:",
    ]
    for f in risk_result.get("findings", []):
        lines.append(f"  - [{f.severity.upper()}] {f.title}: {f.description}")

    lines.append("")
    lines.append("Changed files (patches truncated):")

    budget = _MAX_EVIDENCE_CHARS - len("\n".join(lines))
    for cf in changed_files:
        entry = f"  {_sanitize(cf.get('filename', ''))} ({cf.get('status', '')} +{cf.get('additions', 0)}/-{cf.get('deletions', 0)})"
        patch = cf.get("patch", "")
        if patch:
            truncated = _sanitize(patch[:800])
            entry += f"\n    {truncated}"
        if len(entry) > budget:
            lines.append("  ... [remaining files omitted for brevity]")
            break
        lines.append(entry)
        budget -= len(entry)

    return "\n".join(lines)


_SYSTEM_PROMPT = """You are PRism, a code review risk analysis assistant.
You receive deterministic analysis results and PR evidence. Your job is to:
1. Summarize the key risks and notable changes in 2-4 concise paragraphs.
2. Note any patterns the deterministic analyzer may have missed.
3. Be factual — only reference files and changes present in the evidence.
4. Never fabricate file names, line numbers, vulnerabilities, or repository facts.
5. Never suggest approving, merging, or rejecting the PR.
6. Never execute code or suggest running commands.
Respond ONLY with your analysis text. No JSON, no markdown fences."""


async def generate_ai_summary(
    pr_meta: PullRequestInfo,
    changed_files: list[dict],
    risk_result: dict,
) -> Tuple[str | None, str]:
    """Generate an AI summary using Gemma 4 via Google AI Studio.

    Returns (summary_text, status) where status is one of:
    - "available"   — model responded successfully
    - "unavailable" — credentials not configured
    - "error"       — model call failed
    - "disabled"    — AI explicitly disabled
    """
    if os.environ.get("PRISM_AI_DISABLED", "").lower() in ("1", "true", "yes"):
        return None, "disabled"

    api_key = os.environ.get("GOOGLE_AI_API_KEY", "").strip()
    if not api_key:
        logger.info("GOOGLE_AI_API_KEY not set — AI summary unavailable")
        return None, "unavailable"

    evidence = _build_evidence_summary(pr_meta, changed_files, risk_result)

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=_GEMMA_MODEL,
            contents=evidence,
            config=genai.types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                max_output_tokens=1024,
                temperature=0.3,
            ),
        )

        text = response.text
        if not text or len(text.strip()) < 20:
            logger.warning("Gemma 4 returned empty or very short response")
            return None, "error"

        return text.strip(), "available"

    except ImportError:
        logger.error("google-genai package not installed")
        return None, "error"
    except Exception as exc:
        logger.error("Gemma 4 API call failed: %s", exc)
        return None, "error"

