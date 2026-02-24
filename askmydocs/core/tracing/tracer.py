"""
askmydocs.core.tracing.tracer

Strict, low-overhead stage-level tracing for a single request.

Public surface:
- Tracer.start_trace(request_id, metadata) -> Trace
- Trace.span(stage_name, metadata=None) -> span context manager (sync + async)
- Trace.mark(stage_name, metadata=None, duration_ns=None) -> record externally measured step
- Trace.finish() -> TraceRecord

Design principles:
- Monotonic clock only (durations are reliable; wall-clock isn't).
- Strict correctness: structural misuse raises exceptions immediately.
- Async-first: works with `async with` and parallel pipelines.
- Minimal overhead: tiny objects, no heavy deps, no I/O here.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from ..config import TracingConfig
from ..errors import InvalidSpanError, SpanHierarchyError, TracingError, SLAViolationError
from ..types import SpanRecord, Tags, TraceRecord, SLAResult
from .stats import StatsAggregator
from .sla import SLARegistry
from contextlib import asynccontextmanager, contextmanager


def _now_ns() -> int:
    """Fast, monotonic time source in nanoseconds."""
    return time.monotonic_ns()


@dataclass
class _OpenSpan:
    """
    Internal mutable span state while the span is open.
    We only create an immutable SpanRecord when the span closes.
    """
    stage_name: str
    started_at_ns: int
    span_id: int
    parent_span_id: Optional[int]
    metadata: Tags


class _SpanContext:
    """
    A context manager + async context manager representing a single span.

    Why a class?
    - Keeps API ergonomic: `with trace.span(...):`
    - Ensures we always close spans even if exceptions occur
      (we still re-raise exceptions; we just record timing first).
    """

    def __init__(self, trace: "Trace", stage_name: str, metadata: Optional[Tags]):
        self._trace = trace
        self._stage_name = stage_name
        self._metadata = metadata

        self._open_span: Optional[_OpenSpan] = None

    # --- sync context manager ---
    def __enter__(self):
        self._open_span = self._trace._begin_span(self._stage_name, self._metadata)
        return self

    def __exit__(self, exc_type, exc, tb):
        # Always end the span; do not swallow errors from user code.
        self._trace._end_span(self._open_span)
        return False

    # --- async context manager ---
    async def __aenter__(self):
        self._open_span = self._trace._begin_span(self._stage_name, self._metadata)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._trace._end_span(self._open_span)
        return False


class Trace:
    """
    Mutable per-request trace builder.

    Lifecycle:
    - created by Tracer.start_trace(...)
    - user creates spans via trace.span(...)
    - user calls trace.finish() exactly once -> TraceRecord (immutable)
    """

    def __init__(self, request_id: str, metadata: Optional[Tags], config: TracingConfig):
        self._config = config

        self.request_id = request_id
        self.metadata: Tags = metadata or {}

        self.started_at_ns: int = _now_ns()
        self.ended_at_ns: Optional[int] = None

        self._finished: bool = False

        self._next_span_id: int = 1
        self._active_stack: list[int] = []         # stack of open span_ids
        self._spans: list[SpanRecord] = []         # completed spans in close order

        # Optional: map span_id -> stage name (helps error messages / debugging)
        self._span_name_by_id: dict[int, str] = {}

    # ----------------------------
    # Public API
    # ----------------------------

    def span(self, stage_name: str, metadata: Optional[Tags] = None) -> _SpanContext:
        """
        Create a span context manager.

        Works with:
        - `with trace.span(...):`
        - `async with trace.span(...):`
        """
        return _SpanContext(self, stage_name, metadata)

    def mark(
        self,
        stage_name: str,
        metadata: Optional[Tags] = None,
        *,
        duration_ns: Optional[int] = None,
    ) -> None:
        """
        Record an externally-measured step.

        Use when you already measured duration elsewhere, or when you have a
        constant-cost stage and you don't want a context manager.

        Semantics:
        - If duration_ns is None: a 0-duration marker at "now".
        - If duration_ns is provided: we back-compute started_at = now - duration_ns.
        """
        self._ensure_not_finished()

        ended_at = _now_ns()
        if duration_ns is None:
            started_at = ended_at
            duration = 0
        else:
            if duration_ns < 0:
                raise InvalidSpanError(f"duration_ns must be >= 0 (got {duration_ns})")
            started_at = ended_at - duration_ns
            duration = duration_ns

        parent_span_id = self._active_stack[-1] if self._active_stack else None
        span_id = self._alloc_span_id()

        span_metadata = self._maybe_record_metadata(metadata)

        self._spans.append(
            SpanRecord(
                stage_name=stage_name,
                started_at_ns=started_at,
                ended_at_ns=ended_at,
                duration_ns=duration,
                metadata=span_metadata,
                span_id=span_id,
                parent_span_id=parent_span_id,
            )
        )

    def finish(self) -> TraceRecord:
        """
        Finalize this trace and return an immutable TraceRecord.

        Strict behavior:
        - If any spans are still open, raise (do NOT auto-close).
        - After finish, no spans/marks are allowed.
        """
        if self._finished:
            raise TracingError("Trace.finish() called more than once")

        if self._active_stack:
            open_names = [self._span_name_by_id.get(sid, str(sid)) for sid in self._active_stack]
            raise TracingError(
                f"Cannot finish trace with open spans: stack={self._active_stack} names={open_names}"
            )

        self.ended_at_ns = _now_ns()
        total_duration_ns = self.ended_at_ns - self.started_at_ns
        if total_duration_ns < 0:
            # Should never happen with monotonic clock, but keep it defensive.
            raise InvalidSpanError("Trace duration computed negative (clock issue?)")

        self._finished = True

        return TraceRecord(
            request_id=self.request_id,
            started_at_ns=self.started_at_ns,
            ended_at_ns=self.ended_at_ns,
            total_duration_ns=total_duration_ns,
            metadata=self._maybe_record_metadata(self.metadata),
            steps=tuple(self._spans),
        )

    # ----------------------------
    # Internal helpers
    # ----------------------------

    def _ensure_not_finished(self) -> None:
        if self._finished:
            raise TracingError("Cannot record spans/marks after Trace.finish()")

    def _alloc_span_id(self) -> int:
        span_id = self._next_span_id
        self._next_span_id += 1
        return span_id

    def _maybe_record_metadata(self, metadata: Optional[Tags]) -> Tags:
        """
        Respect TracingConfig.record_metadata.

        If disabled, drop metadata to reduce payload size / overhead.
        """
        if not self._config.record_metadata:
            return {}
        return metadata or {}

    def _begin_span(self, stage_name: str, metadata: Optional[Tags]) -> _OpenSpan:
        self._ensure_not_finished()

        span_id = self._alloc_span_id()
        parent_span_id = self._active_stack[-1] if self._active_stack else None

        started_at_ns = _now_ns()
        span_metadata = self._maybe_record_metadata(metadata)

        self._active_stack.append(span_id)
        self._span_name_by_id[span_id] = stage_name

        return _OpenSpan(
            stage_name=stage_name,
            started_at_ns=started_at_ns,
            span_id=span_id,
            parent_span_id=parent_span_id,
            metadata=span_metadata,
        )

    def _end_span(self, open_span: Optional[_OpenSpan]) -> None:
        if open_span is None:
            # Defensive: shouldn't happen in correct usage
            raise TracingError("Attempted to end a span that was never started")

        ended_at_ns = _now_ns()
        duration_ns = ended_at_ns - open_span.started_at_ns

        if duration_ns < 0:
            raise InvalidSpanError(
                f"Negative duration for span '{open_span.stage_name}' "
                f"(started_at_ns={open_span.started_at_ns}, ended_at_ns={ended_at_ns})"
            )

        # Strict stack correctness: the span being closed must be the top of stack.
        if not self._active_stack:
            raise SpanHierarchyError(
                f"Span stack empty while closing span_id={open_span.span_id} "
                f"('{open_span.stage_name}')"
            )

        top = self._active_stack[-1]
        if top != open_span.span_id:
            raise SpanHierarchyError(
                "Span nesting violation: attempting to close span_id="
                f"{open_span.span_id} ('{open_span.stage_name}') "
                f"but stack top is span_id={top} ('{self._span_name_by_id.get(top)}')"
            )

        self._active_stack.pop()

        self._spans.append(
            SpanRecord(
                stage_name=open_span.stage_name,
                started_at_ns=open_span.started_at_ns,
                ended_at_ns=ended_at_ns,
                duration_ns=duration_ns,
                metadata=open_span.metadata,
                span_id=open_span.span_id,
                parent_span_id=open_span.parent_span_id,
            )
        )


class Tracer:
    """
    Factory for per-request Trace objects.

    Tracer itself is lightweight and stateless aside from its config.
    """

    def __init__(
        self,
        config: Optional[TracingConfig] = None,
        *,
        aggregator: Optional["StatsAggregator"] = None,
        sla_registry: Optional["SLARegistry"] = None,
    ):
        self._config = config or TracingConfig()
        self._aggregator = aggregator
        self._sla_registry = sla_registry

    def start_trace(self, request_id: str, metadata: Optional[Tags] = None) -> Trace:
        """
        Start a new trace for a request.

        If tracing is disabled, we still return a Trace that records nothing
        only if you implement a NoopTrace later. For now we keep it strict:
        tracing disabled means you should not call tracer.start_trace().
        """
        if not self._config.enable_tracing:
            raise TracingError("Tracing is disabled by configuration")
        return Trace(request_id=request_id, metadata=metadata, config=self._config)
    
    def _post_process(self, trace_record: TraceRecord) -> Optional[SLAResult]:
        """
        Shared post-processing:
        - add trace to aggregator
        - compute report
        - check SLA
        - optionally raise on violation
        """
        if self._aggregator is None:
            return None

        self._aggregator.add(trace_record)
        report = self._aggregator.report()

        if self._sla_registry is None:
            return None

        result = self._sla_registry.check(report)

        if not result.ok and self._sla_registry.config.fail_fast:
            # Raise the first violation (deterministic order depends on dict insertion).
            stage_name, metrics = next(iter(result.violations.items()))
            metric_name, observed_value = next(iter(metrics.items()))
            raise SLAViolationError(stage_name, metric_name, observed_value)

        return result
    
    @contextmanager
    def request(self, request_id: str, metadata: Optional[Tags] = None):
        """
        Sync request context manager.

        Usage:
            with tracer.request("req-1") as trace:
                with trace.span("retrieve"): ...
        """
        trace = self.start_trace(request_id, metadata)
        try:
            yield trace
        finally:
            trace_record = trace.finish()
            self._post_process(trace_record)

    @asynccontextmanager
    async def arequest(self, request_id: str, metadata: Optional[Tags] = None):
        """
        Async request context manager.

        Usage:
            async with tracer.arequest("req-1") as trace:
                async with trace.span("retrieve"): ...
        """
        trace = self.start_trace(request_id, metadata)
        try:
            yield trace
        finally:
            trace_record = trace.finish()
            self._post_process(trace_record)