from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

# Tags are lightweight metadata attached to traces/spans.
# Design choice: flexible key/value labels (tenant, cache_hit, index, etc.)
# so we can slice latency later without changing schemas.
Tags = Dict[str, Any]


@dataclass(frozen=True)
class SpanRecord:
    """
    One timed stage inside a request (e.g., 'retrieve', 'rerank').

    Design choices:
    - Monotonic timestamps in ns: stable for duration measurement (not wall clock).
    - duration_ns stored explicitly: avoids recompute during aggregation/export.
    - parent_span_id: enables nested spans and parallel branch trees.
    - metadata: stage-level labels for later breakdowns.
    """
    stage_name: str
    started_at_ns: int
    ended_at_ns: int
    duration_ns: int
    metadata: Tags
    span_id: int
    parent_span_id: Optional[int] = None


@dataclass(frozen=True)
class TraceRecord:
    """
    One request timeline, containing many SpanRecords.

    Design choices:
    - Groups all stage timings under a request_id for JSONL export and debugging.
    - total_duration_ns stored explicitly for fast end-to-end metrics.
    - steps is a tuple: immutability helps treat completed traces as historical facts.
    """
    request_id: str
    started_at_ns: int
    ended_at_ns: int
    total_duration_ns: int
    metadata: Tags
    steps: tuple[SpanRecord, ...]


@dataclass(frozen=True)
class StageStats:
    """
    Aggregated latency distribution for a single stage across many traces.

    Design choice:
    - Store percentiles (p50/p95/p99) only, not raw samples, to keep reporting light.
    """
    count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float


@dataclass(frozen=True)
class Report:
    """
    Snapshot of system performance across stages.

    Design choices:
    - stages is a dict for O(1) lookup by stage name.
    - generated_at_ns lets us time-stamp snapshots for periodic metrics.json exports.
    """
    stages: dict[str, StageStats]
    generated_at_ns: int


@dataclass(frozen=True)
class StageSLA:
    """
    Performance budgets for a stage.

    Design choices:
    - Optional thresholds: some stages may have only p95 targets, others p99 too.
    - Named 'max_*' to make direction explicit (smaller is better).
    """
    max_p95_ms: Optional[float] = None
    max_p99_ms: Optional[float] = None


@dataclass(frozen=True)
class SLAResult:
    """
    Outcome of comparing a Report against StageSLA budgets.

    Design choice:
    - violations carries machine-readable values (e.g., measured p95_ms),
      useful for logging/alerts/Prometheus later.
    """
    ok: bool
    violations: dict[str, dict[str, float]]