import time
import asyncio
import pytest

from askmydocs.core.config import SLAConfig, TracingConfig
from askmydocs.core.errors import SLAViolationError, TracingError
from askmydocs.core.tracing.stats import StatsAggregator
from askmydocs.core.tracing.sla import SLARegistry
from askmydocs.core.tracing.tracer import Tracer
from askmydocs.core.types import StageSLA
from askmydocs.core.tracing.exporter import JSONExporter


# --------------------------------------------
# 1) Basic sync tracing + aggregation
# --------------------------------------------

def test_sync_tracing_and_aggregation():
    agg = StatsAggregator(window_size=5000)
    sla = SLARegistry(SLAConfig(stage_budgets={}, fail_fast=False))

    tracer = Tracer(
        TracingConfig(enable_tracing=True),
        aggregator=agg,
        sla_registry=sla,
    )

    with tracer.request("req-1") as trace:
        with trace.span("retrieve"):
            time.sleep(0.002)
        with trace.span("rerank"):
            time.sleep(0.001)

    report = agg.report()

    assert "retrieve" in report.stages
    assert "rerank" in report.stages
    assert report.stages["retrieve"].count == 1
    assert report.stages["rerank"].count == 1
    assert report.stages["retrieve"].p50_ms > 0


# --------------------------------------------
# 2) SLA fail-fast behavior
# --------------------------------------------

def test_sla_fail_fast():
    agg = StatsAggregator(window_size=5000)

    budgets = {
        "retrieve": StageSLA(max_p95_ms=0.1)  # unrealistically low
    }

    sla = SLARegistry(SLAConfig(stage_budgets=budgets, fail_fast=True))

    tracer = Tracer(
        TracingConfig(enable_tracing=True),
        aggregator=agg,
        sla_registry=sla,
    )

    with pytest.raises(SLAViolationError):
        with tracer.request("req-2") as trace:
            with trace.span("retrieve"):
                time.sleep(0.002)


# --------------------------------------------
# 3) Async + parallel spans
# --------------------------------------------

@pytest.mark.asyncio
async def test_async_parallel_spans():
    agg = StatsAggregator(window_size=5000)
    sla = SLARegistry(SLAConfig(stage_budgets={}, fail_fast=False))
    exporter = JSONExporter(trace_path="test_trace.jsonl", metrics_path="test_metrics.json")

    tracer = Tracer(
        TracingConfig(enable_tracing=True),
        aggregator=agg,
        sla_registry=sla,
        exporter=exporter,
    )

    async def vec(trace):
        async with trace.span("vector_search"):
            await asyncio.sleep(0.01)

    async def bm25(trace):
        async with trace.span("bm25_search"):
            await asyncio.sleep(0.008)

    async with tracer.arequest("req-3") as trace:
        async with trace.span("hybrid_search"):
            await asyncio.gather(vec(trace), bm25(trace))

    report = agg.report()

    assert "hybrid_search" in report.stages
    assert "vector_search" in report.stages
    assert "bm25_search" in report.stages


# --------------------------------------------
# 4) Strict error if span left open
# --------------------------------------------

def test_finish_raises_if_span_left_open():
    tracer = Tracer(TracingConfig(enable_tracing=True))

    with pytest.raises(TracingError):
        with tracer.request("req-4") as trace:
            ctx = trace.span("oops")
            ctx.__enter__()  # manually open
            # do not close → finish() should raise