from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


Severity = Literal["low", "medium", "high"]
SafetyAction = Literal["allow", "reject", "quarantine"]


@dataclass(frozen=True)
class ScanFinding:
    """
    Represents one safety issue detected during ingestion.

    Examples:
    - NSFW phrase detected
    - API key pattern detected
    - Prompt injection instruction detected
    """

    category: str
    severity: Severity
    message: str
    span: Optional[tuple[int, int]] = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SafetyScanResult:
    """
    Aggregated output of one or more safety scanners.

    Design notes:
    - findings contains the detailed issues found by validators/scanners.
    - category_counts helps policy code reason about how many findings of each
      type were detected.
    - risk_score is a simple normalized score in the range [0.0, 1.0].
    """

    findings: list[ScanFinding] = field(default_factory=list)
    category_counts: dict[str, int] = field(default_factory=dict)
    risk_score: float = 0.0

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)


@dataclass(frozen=True)
class SafetyDecision:
    """
    Final policy decision produced after evaluating a SafetyScanResult.

    Actions:
    - allow: continue ingestion
    - reject: stop ingestion and surface an error
    - quarantine: do not index, but preserve an auditable decision
    """

    action: SafetyAction
    reason: str
    findings: list[ScanFinding] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def is_allowed(self) -> bool:
        return self.action == "allow"

    @property
    def is_rejected(self) -> bool:
        return self.action == "reject"

    @property
    def is_quarantined(self) -> bool:
        return self.action == "quarantine"

    @property
    def allowed(self) -> bool:
        """
        Backward-compatible alias for pipeline usage.
        """
        return self.is_allowed