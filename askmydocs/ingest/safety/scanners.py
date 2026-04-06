from __future__ import annotations

import re

from askmydocs.ingest.safety.types import ScanFinding, SafetyScanResult


# ------------------------------
# Pattern Definitions
# ------------------------------

# Basic NSFW keyword list (minimal v1 implementation)
NSFW_KEYWORDS = [
    "porn",
    "xxx",
    "explicit sex",
    "hardcore",
    "adult video",
]

# Secret / credential patterns
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS key
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # API keys
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*"),
]

# Prompt injection indicators
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore previous instructions", re.IGNORECASE),
    re.compile(r"system prompt", re.IGNORECASE),
    re.compile(r"developer message", re.IGNORECASE),
    re.compile(r"do not follow earlier instructions", re.IGNORECASE),
]

# TODO: Combine regex patterns into a single compiled regex to reduce multiple passes over text
# TODO: Implement incremental scanning based on document diff (scan only changed segments)
# TODO: Add parallel scanning across categories for improved performance
# TODO: Add structured location metadata (line number, page number) instead of span indices


# ------------------------------
# Scanner Functions
# ------------------------------


def scan_nsfw(text: str) -> list[ScanFinding]:
    """
    Detect simple NSFW content using keyword matching.
    """

    findings: list[ScanFinding] = []

    # lower_text = text.lower()

    for keyword in NSFW_KEYWORDS:
        if keyword in text:
            findings.append(
                ScanFinding(
                    category="nsfw",
                    severity="medium",
                    message=f"NSFW keyword detected: {keyword} (location: unknown)",
                )
            )

    return findings


def scan_secrets(text: str) -> list[ScanFinding]:
    """
    Detect possible secrets or credentials.
    """

    findings: list[ScanFinding] = []

    for pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                ScanFinding(
                    category="secret",
                    severity="high",
                    message=f"Possible credential detected at span {match.start()}-{match.end()}",
                    span=(match.start(), match.end()),
                )
            )

    return findings


def scan_prompt_injection(text: str) -> list[ScanFinding]:
    """
    Detect prompt injection style instructions.
    """

    findings: list[ScanFinding] = []

    for pattern in PROMPT_INJECTION_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                ScanFinding(
                    category="prompt_injection",
                    severity="high",
                    message=f"Prompt injection pattern detected at span {match.start()}-{match.end()}",
                    span=(match.start(), match.end()),
                )
            )

    return findings


# ------------------------------
# Aggregate Scanner
# ------------------------------


def scan_text(text: str) -> SafetyScanResult:
    """
    Run all safety scanners on the given text.
    """

    # TODO: If scan fails (high severity), pipeline should skip downstream processing (split/chunk)

    findings: list[ScanFinding] = []
    lower_text = text.lower()

    # NSFW scan (medium severity)
    findings.extend(scan_nsfw(lower_text))

    # Secret scan (high severity, early exit if found)
    secret_findings = scan_secrets(text)
    if secret_findings:
        findings.extend(secret_findings)
        return SafetyScanResult(
            findings=findings,
            category_counts={"secret": len(secret_findings)},
            risk_score=1.0,
        )

    # Prompt injection scan (high severity, early exit if found)
    prompt_findings = scan_prompt_injection(text)
    if prompt_findings:
        findings.extend(prompt_findings)
        return SafetyScanResult(
            findings=findings,
            category_counts={"prompt_injection": len(prompt_findings)},
            risk_score=1.0,
        )

    # Aggregate category counts
    category_counts: dict[str, int] = {}

    for finding in findings:
        category_counts[finding.category] = category_counts.get(finding.category, 0) + 1

    # Simple risk score calculation
    risk_score = min(1.0, len(findings) * 0.2)

    return SafetyScanResult(
        findings=findings,
        category_counts=category_counts,
        risk_score=risk_score,
    )


# -------------------------------------------------
# Class Wrapper (for pipeline compatibility)
# -------------------------------------------------


class SafetyScanner:
    """
    Wrapper around scan_text to provide a class-based interface
    compatible with the ingestion pipeline.
    """

    def __init__(self) -> None:
        pass

    def scan(self, text: str) -> SafetyScanResult:
        """
        Run all safety scanners on the given text.
        """
        return scan_text(text)