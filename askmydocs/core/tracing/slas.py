"""
askmydocs.core.tracing.sla

Stage-level SLA comparison logic.

Pure comparison layer:
- Takes aggregated Report
- Applies StageSLA budgets
- Returns SLAResult
"""

from __future__ import annotations

from typing import Dict

from ..config import SLAConfig
from ..types import Report, SLAResult, StageSLA


class SLARegistry:
    """
    Compares aggregated performance against configured SLAs.

    Design principles:
    - Pure logic (no side effects)
    - No percentile computation here
    - No raising inside this layer
    """

    def __init__(self, config: SLAConfig):
        self._config = config

    @property
    def config(self) -> SLAConfig:
        return self._config

    def check(self, report: Report) -> SLAResult:
        """
        Compare Report against configured StageSLA budgets.

        Returns:
            SLAResult(ok=bool, violations=dict)
        """
        violations: Dict[str, Dict[str, float]] = {}

        for stage_name, stage_sla in self._config.stage_budgets.items():
            stage_stats = report.stages.get(stage_name)

            # If stage not present in report, skip.
            if stage_stats is None:
                continue

            stage_violations: Dict[str, float] = {}

            # Check p95
            if (
                stage_sla.max_p95_ms is not None
                and stage_stats.p95_ms > stage_sla.max_p95_ms
            ):
                stage_violations["p95_ms"] = stage_stats.p95_ms

            # Check p99
            if (
                stage_sla.max_p99_ms is not None
                and stage_stats.p99_ms > stage_sla.max_p99_ms
            ):
                stage_violations["p99_ms"] = stage_stats.p99_ms

            if stage_violations:
                violations[stage_name] = stage_violations

        ok = len(violations) == 0

        return SLAResult(ok=ok, violations=violations)