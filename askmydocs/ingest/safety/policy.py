from __future__ import annotations

from askmydocs.ingest.safety.types import SafetyDecision, SafetyScanResult


# ------------------------------
# Policy Thresholds
# ------------------------------

# Severity levels that trigger automatic rejection
REJECT_SEVERITIES = {"high"}

# Severity levels that trigger quarantine
QUARANTINE_SEVERITIES = {"medium"}


# ------------------------------
# Policy Evaluation
# ------------------------------


def evaluate_policy(scan_result: SafetyScanResult) -> SafetyDecision:
    """
    Evaluate the scan result and produce a final safety decision.

    Decision rules (v1):

    - If any HIGH severity finding exists → reject
    - Else if any MEDIUM severity finding exists → quarantine
    - Otherwise → allow
    """

    if not scan_result.findings:
        return SafetyDecision(
            action="allow",
            reason="no_findings",
        )

    highest_severity = "low"

    for finding in scan_result.findings:
        if finding.severity == "high":
            highest_severity = "high"
            break
        elif finding.severity == "medium":
            highest_severity = "medium"

    if highest_severity in REJECT_SEVERITIES:
        return SafetyDecision(
            action="reject",
            reason="high_severity_finding",
            findings=scan_result.findings,
        )

    if highest_severity in QUARANTINE_SEVERITIES:
        return SafetyDecision(
            action="quarantine",
            reason="medium_severity_finding",
            findings=scan_result.findings,
        )

    return SafetyDecision(
        action="allow",
        reason="low_risk",
        findings=scan_result.findings,
    )
