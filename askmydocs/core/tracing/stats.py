"""
askmydocs.core.tracing.stats

Stage-level performance aggregation.

Responsibilities:
- Accept completed TraceRecord objects
- Maintain rolling window of stage durations
- Compute exact percentiles (p50, p95, p99)
- Produce Report snapshots

Design principles:
- Exact percentile (no approximation)
- Rolling window per stage (bounded memory)
- Pure in-memory aggregation
- No SLA logic here
"""

from __future__ import annotations

import math
from collections import deque
from typing import Dict

from ..types import Report, StageStats, TraceRecord


class StatsAggregator:
    """
    Aggregates span durations per stage using a rolling window.

    Design choices:
    - One deque per stage_name
    - Each deque has fixed maxlen (window_size)
    - Percentiles computed on-demand in report()
    - Exact percentile via sorted copy
    """

    def __init__(self, window_size: int = 5000):
        if window_size <= 0:
            raise ValueError("window_size must be > 0")

        self._window_size = window_size

        # stage_name -> deque[float] (durations in milliseconds)
        self._data: Dict[str, deque[float]] = {}

    # ----------------------------
    # Public API
    # ----------------------------

    def add(self, trace: TraceRecord) -> None:
        """
        Ingest a completed TraceRecord.

        Extracts all SpanRecord durations and stores them per stage.
        """

        for span in trace.steps:
            stage_name = span.stage_name

            duration_ms = span.duration_ns / 1_000_000.0

            if stage_name not in self._data:
                self._data[stage_name] = deque(maxlen=self._window_size)

            self._data[stage_name].append(duration_ms)

    def report(self) -> Report:
        """
        Compute current percentile snapshot across all stages.

        Returns:
            Report containing StageStats per stage.
        """

        stage_stats: Dict[str, StageStats] = {}

        for stage_name, durations in self._data.items():
            if not durations:
                continue

            values = sorted(durations)
            count = len(values)

            p50 = self._percentile(values, 0.50)
            p95 = self._percentile(values, 0.95)
            p99 = self._percentile(values, 0.99)

            stage_stats[stage_name] = StageStats(
                count=count,
                p50_ms=p50,
                p95_ms=p95,
                p99_ms=p99,
            )

        return Report(
            stages=stage_stats,
            # TODO: Use real monotonic time for generated_at_ns in future
            generated_at_ns=0,  # We can later plug real monotonic time here if needed
        )

    # ----------------------------
    # Internal helpers
    # ----------------------------

    @staticmethod
    def _percentile(sorted_values: list[float], p: float) -> float:
        """
        Compute exact percentile using nearest-rank method.

        Assumes sorted_values is already sorted.
        """

        if not sorted_values:
            return 0.0

        n = len(sorted_values)

        # nearest rank method
        index = math.ceil(p * n) - 1
        index = max(0, min(index, n - 1))

        return sorted_values[index]