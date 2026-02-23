from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .types import StageSLA


# ----------------------------
# Tracing / Instrumentation
# ----------------------------

@dataclass(frozen=True)
class TracingConfig:
    """
    Controls instrumentation behavior.

    Design choices:
    - enable_tracing: allows completely disabling tracing if needed.
    - record_metadata: toggle to reduce payload size (context budget control).
    - overhead_budget_ms: guardrail for instrumentation latency overhead.
    """
    enable_tracing: bool = True
    record_metadata: bool = True
    overhead_budget_ms: float = 2.0


# ----------------------------
# SLA Policy
# ----------------------------

@dataclass(frozen=True)
class SLAConfig:
    """
    Defines stage-level performance budgets and enforcement behavior.

    Design choices:
    - stage_budgets: mapping stage_name -> StageSLA
    - fail_fast: if True, raises exception on SLA violation.
      Useful for CI or strict enforcement scenarios.
    """
    stage_budgets: Dict[str, StageSLA] = field(default_factory=dict)
    fail_fast: bool = False


# ----------------------------
# Export / Observability
# ----------------------------

@dataclass(frozen=True)
class ExportConfig:
    """
    Controls output destinations and observability toggles.

    Design choices:
    - jsonl_path / metrics_path: local fallback storage.
    - enable_prometheus / enable_otel: future integrations.
    - keep minimal flags to reduce cognitive load.
    """
    jsonl_path: str = "trace.jsonl"
    metrics_path: str = "metrics.json"
    enable_prometheus: bool = False
    enable_otel: bool = False