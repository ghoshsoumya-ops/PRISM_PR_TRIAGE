"""Deterministic risk analyzer — scores PRs based on verifiable evidence."""

from __future__ import annotations

from .schemas import Finding, PullRequestInfo

SENSITIVE_PATTERNS: list[tuple[str, str, str]] = [
    (".env", "security", "Environment/secrets file modified"),
    (".pem", "security", "Certificate or private key file modified"),
    (".key", "security", "Private key file modified"),
    ("secret", "security", "File with 'secret' in name modified"),
    ("password", "security", "File with 'password' in name modified"),
    ("credential", "security", "File with 'credential' in name modified"),
    ("auth", "security", "Authentication-related file modified"),
    ("token", "security", "Token-related file modified"),
    (".github/workflows/", "cicd", "CI/CD workflow modified"),
    ("Dockerfile", "cicd", "Docker configuration modified"),
    ("docker-compose", "cicd", "Docker Compose configuration modified"),
    (".gitlab-ci", "cicd", "CI pipeline modified"),
    ("Jenkinsfile", "cicd", "Jenkins pipeline modified"),
    ("package-lock.json", "dependency", "npm lockfile modified"),
    ("yarn.lock", "dependency", "Yarn lockfile modified"),
    ("pnpm-lock.yaml", "dependency", "pnpm lockfile modified"),
    ("requirements.txt", "dependency", "Python requirements modified"),
    ("Pipfile.lock", "dependency", "Pipfile lockfile modified"),
    ("poetry.lock", "dependency", "Poetry lockfile modified"),
    ("go.sum", "dependency", "Go dependency checksums modified"),
    ("Gemfile.lock", "dependency", "Ruby Gemfile lockfile modified"),
    ("package.json", "dependency", "npm package manifest modified"),
    ("Pipfile", "dependency", "Python Pipfile modified"),
    ("pyproject.toml", "dependency", "Python project config modified"),
    ("Cargo.toml", "dependency", "Rust dependencies modified"),
    ("go.mod", "dependency", "Go module dependencies modified"),
    ("Gemfile", "dependency", "Ruby dependencies modified"),
    ("CODEOWNERS", "permission", "Code ownership rules modified"),
    (".gitignore", "config", "Git ignore rules modified"),
    ("permissions", "permission", "Permission-related file modified"),
    ("rbac", "permission", "RBAC configuration modified"),
    ("policy", "permission", "Policy file modified"),
]


def _check_sensitive_files(changed_files: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    for f in changed_files:
        filename = f.get("filename", "").lower()
        for pattern, category, desc in SENSITIVE_PATTERNS:
            if pattern.lower() in filename:
                severity = "high" if category == "security" else "medium"
                findings.append(
                    Finding(
                        category=category,
                        severity=severity,
                        title=desc,
                        description=f"The file `{f.get('filename', '')}` was {f.get('status', 'modified')}.",
                        file=f.get("filename"),
                    )
                )
                break
    return findings


def _check_change_size(
    pr_meta: PullRequestInfo, changed_files: list[dict]
) -> list[Finding]:
    findings: list[Finding] = []
    total_changes = pr_meta.additions + pr_meta.deletions

    if total_changes > 1000:
        findings.append(
            Finding(
                category="size",
                severity="high" if total_changes > 3000 else "medium",
                title="Very large change",
                description=(
                    f"This PR modifies {total_changes:,} lines "
                    f"(+{pr_meta.additions:,} / -{pr_meta.deletions:,}) "
                    f"across {pr_meta.changed_files} files. "
                    "Large changes are harder to review thoroughly."
                ),
            )
        )
    elif total_changes > 500:
        findings.append(
            Finding(
                category="size",
                severity="low",
                title="Moderately large change",
                description=(
                    f"This PR modifies {total_changes:,} lines across "
                    f"{pr_meta.changed_files} files."
                ),
            )
        )

    if pr_meta.changed_files > 50:
        findings.append(
            Finding(
                category="size",
                severity="medium",
                title="Many files changed",
                description=(
                    f"{pr_meta.changed_files} files were changed. "
                    "PRs touching many files can be difficult to review."
                ),
            )
        )

    # Single-file massive changes
    for f in changed_files:
        file_changes = f.get("additions", 0) + f.get("deletions", 0)
        if file_changes > 500:
            findings.append(
                Finding(
                    category="size",
                    severity="medium",
                    title=f"Large single-file change ({file_changes:,} lines)",
                    description=f"The file `{f.get('filename', '')}` has {file_changes:,} lines changed.",
                    file=f.get("filename"),
                )
            )

    return findings


def _check_empty_diff(changed_files: list[dict]) -> list[Finding]:
    if not changed_files:
        return [
            Finding(
                category="evidence",
                severity="medium",
                title="No changed files retrieved",
                description=(
                    "No file changes were returned by the GitHub API. "
                    "This may indicate the PR has no code changes, "
                    "or API access was limited."
                ),
            )
        ]

    empty_patches = [f for f in changed_files if not f.get("patch")]
    if len(empty_patches) > len(changed_files) * 0.5 and len(empty_patches) > 2:
        return [
            Finding(
                category="evidence",
                severity="low",
                title="Many files have no visible diff",
                description=(
                    f"{len(empty_patches)} of {len(changed_files)} changed files "
                    "have no patch content. These may be binary files or "
                    "files too large for inline diffs."
                ),
            )
        ]
    return []


def _check_binary_and_generated(changed_files: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    binary_exts = {".exe", ".dll", ".so", ".dylib", ".bin", ".wasm", ".jar", ".war"}
    for f in changed_files:
        filename = f.get("filename", "")
        lower = filename.lower()
        for ext in binary_exts:
            if lower.endswith(ext):
                findings.append(
                    Finding(
                        category="security",
                        severity="high",
                        title="Binary file modified",
                        description=(
                            f"The binary file `{filename}` was {f.get('status', 'modified')}. "
                            "Binary files cannot be reviewed in diffs."
                        ),
                        file=filename,
                    )
                )
                break
    return findings


def _calculate_score(findings: list[Finding]) -> int:
    severity_weights = {"critical": 30, "high": 20, "medium": 10, "low": 5}
    score = 0
    for f in findings:
        score += severity_weights.get(f.severity, 5)
    return min(score, 100)


def _determine_level(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 45:
        return "high"
    if score >= 20:
        return "medium"
    return "low"


def _generate_recommendations(
    findings: list[Finding], pr_meta: PullRequestInfo
) -> list[str]:
    recommendations: list[str] = []
    categories = {f.category for f in findings}
    severities = {f.severity for f in findings}

    if "security" in categories:
        recommendations.append(
            "Review security-sensitive file changes carefully before merging."
        )
    if "cicd" in categories:
        recommendations.append(
            "Verify CI/CD workflow changes do not introduce unauthorized pipeline steps."
        )
    if "dependency" in categories:
        recommendations.append(
            "Check dependency changes for unexpected additions or version downgrades."
        )
    if "permission" in categories:
        recommendations.append(
            "Confirm permission or ownership changes are intentional."
        )
    if "size" in categories:
        recommendations.append(
            "Consider breaking large changes into smaller, reviewable PRs."
        )
    if "evidence" in categories:
        recommendations.append(
            "Investigate files with missing diffs — they may contain meaningful changes."
        )
    if "critical" in severities or "high" in severities:
        recommendations.append(
            "This PR warrants careful review by a senior team member."
        )
    if not recommendations:
        recommendations.append(
            "No significant risks detected. Standard review process is appropriate."
        )
    return recommendations


def analyze_risk(
    pr_meta: PullRequestInfo, changed_files: list[dict]
) -> dict:
    """Run all deterministic risk checks and return a structured result."""
    findings: list[Finding] = []
    findings.extend(_check_sensitive_files(changed_files))
    findings.extend(_check_change_size(pr_meta, changed_files))
    findings.extend(_check_empty_diff(changed_files))
    findings.extend(_check_binary_and_generated(changed_files))

    score = _calculate_score(findings)
    level = _determine_level(score)
    recommendations = _generate_recommendations(findings, pr_meta)

    return {
        "risk_score": score,
        "risk_level": level,
        "findings": findings,
        "recommendations": recommendations,
    }

