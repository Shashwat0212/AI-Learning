from pathlib import Path

import json
from datetime import datetime

# Helper to ensure test file exists and return its path
def get_test_file_path():
    # Resolves the path to the test file relative to this test file location
    base_dir = Path(__file__).resolve().parent / "test_data"
    # Ensure test_data directory exists
    base_dir.mkdir(parents=True, exist_ok=True)
    file_path = base_dir / "file.txt"

    # NOTE: Do not auto-create or modify file for now (tests expect existing file)

    return str(file_path)

# Global test report dictionary
TEST_REPORT = {}

# Helper for test reporting
def log_test_result(test_name, details):
    TEST_REPORT.setdefault(test_name, []).append(details)
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


# --------------------------------------------
# 5) Ingestion baseline test
# --------------------------------------------

from askmydocs.ingest.pipeline import build_default_pipeline
from askmydocs.ingest.loaders.text_loader import TextLoader
from askmydocs.ingest.splitters.fixed_token import FixedTokenSplitter
import shutil
import os


def test_ingestion_baseline():
    file_path = get_test_file_path()

    with open(file_path, "r") as f:
        content = f.read()

    # Initialize loader with tenant context
    loader = TextLoader(tenant_id="test")
    # Initialize splitter with consistent token size
    splitter = FixedTokenSplitter(target_tokens=50, overlap=0)

    # Build full ingestion pipeline
    pipeline = build_default_pipeline(loader, splitter)

    # Execute ingestion pipeline on file
    chunks = list(pipeline.run([file_path]))

    log_test_result("test_ingestion_baseline", {
        "chunks_count": len(chunks),
        "sample_chunk": str(chunks[0]) if chunks else None,
        "char_count": len(content),
        "approx_tokens": len(content.split()),
        "chunks": [
            {
                "text_length": len(c.text) if hasattr(c, "text") else None,
                "fingerprint": str(c.fingerprint),
                "metadata": getattr(c, "metadata", None)
            }
            for c in chunks
        ]
    })

    # Ensure chunks are generated from file
    print("Chunks generated:", len(chunks))
    print("Sample chunk:", chunks[0] if chunks else None)
    assert len(chunks) > 0

    # Each chunk should have a fingerprint assigned
    for chunk in chunks:
        print("Chunk fingerprint:", chunk.fingerprint)
        print("Chunk metadata:", getattr(chunk, 'metadata', None))
        assert chunk.fingerprint is not None

    # Retrieve trace recorded during pipeline execution
    trace = pipeline.tracer.get_last_trace()
    print("Trace object:", trace)
    assert trace is not None

    # Extract stage names from trace for verification
    stage_names = [s.stage_name for s in trace.steps]
    print("Stages recorded:", stage_names)

    assert "ingest.split" in stage_names
    assert "ingest.enrich" in stage_names
    assert "ingest.fingerprint" in stage_names


# --------------------------------------------
# 6) Incremental ingestion (no change)
# --------------------------------------------


def test_ingestion_incremental_no_change():
    file_path = get_test_file_path()

    # Reset cache to simulate fresh start
    if os.path.exists("cache"):
        shutil.rmtree("cache")

    # First run builds cache
    loader = TextLoader(tenant_id="test")
    splitter = FixedTokenSplitter(target_tokens=50, overlap=0)

    pipeline = build_default_pipeline(loader, splitter)
    pipeline.mode = "incremental"

    # First run builds cache
    _ = list(pipeline.run([file_path]))
    print("Initial run completed (cache built)")

    # Second run should detect no changes
    chunks = list(pipeline.run([file_path]))
    print("Chunks after second run:", chunks)

    log_test_result("test_ingestion_incremental_no_change", {
        "chunks_after_second_run": len(chunks),
        "chunks_data": [str(c) for c in chunks]
    })

    # No new chunks expected since file unchanged
    assert len(chunks) == 0


# --------------------------------------------
# 7) Incremental ingestion (with change)
# --------------------------------------------


def test_ingestion_incremental_with_change():
    file_path = get_test_file_path()

    # Reset cache to ensure clean incremental test
    if os.path.exists("cache"):
        shutil.rmtree("cache")

    # Initial run to populate cache
    loader = TextLoader(tenant_id="test")
    splitter = FixedTokenSplitter(target_tokens=50, overlap=0)

    pipeline = build_default_pipeline(loader, splitter)
    pipeline.mode = "incremental"

    _ = list(pipeline.run([file_path]))
    print("Initial run completed (cache built)")

    # Save original content before modifying
    with open(file_path, "r") as f:
        original_content = f.read()

    # Modify file to simulate new content
    with open(file_path, "a") as f:
        f.write("\nThis is a newly added sentence for incremental testing.")
    print("File modified for incremental test")

    # Run pipeline again to detect changes
    chunks = list(pipeline.run([file_path]))
    print("Chunks after modification:", chunks)

    log_test_result("test_ingestion_incremental_with_change", {
        "chunks_after_modification": len(chunks),
        "chunks_data": [str(c) for c in chunks]
    })

    # Expect new chunks due to file modification
    assert len(chunks) > 0

    # Restore original file content
    with open(file_path, "w") as f:
        f.write(original_content)


# --------------------------------------------
# 8) Stats + SLA integration test
# --------------------------------------------


def test_ingestion_stats_and_sla():
    file_path = get_test_file_path()

    # Initialize stats aggregator
    agg = StatsAggregator(window_size=5000)
    # Initialize SLA registry (no strict limits)
    sla = SLARegistry(SLAConfig(stage_budgets={}, fail_fast=False))

    # Create tracer with aggregator and SLA integration
    tracer = Tracer(
        TracingConfig(enable_tracing=True),
        aggregator=agg,
        sla_registry=sla,
    )

    loader = TextLoader(tenant_id="test")
    splitter = FixedTokenSplitter(target_tokens=50, overlap=0)

    with open(file_path, "r") as f:
        content = f.read()

    pipeline = build_default_pipeline(loader, splitter)
    # Inject custom tracer into pipeline
    pipeline.tracer = tracer

    # Execute pipeline to generate trace data
    _ = list(pipeline.run([file_path]))

    # Generate stats report from aggregator
    print("Generating stats report...")
    report = agg.report()
    print("Report stages:", report.stages)

    log_test_result("test_ingestion_stats_and_sla", {
        "stages": list(report.stages.keys()),
        "stats": {k: {
            "p50": v.p50_ms,
            "p95": v.p95_ms,
            "p99": v.p99_ms,
            "count": v.count
        } for k, v in report.stages.items()},
        "char_count": len(content),
        "approx_tokens": len(content.split()),
        "total_latency_ms": report.stages.get("ingest.document").p50_ms if report.stages.get("ingest.document") else None
    })

    # Ensure stats were collected for at least one stage
    assert len(report.stages) > 0

    # Validate percentile metrics for each stage
    for stats in report.stages.values():
        print("Stage stats:", stats)
        assert stats.p95_ms >= 0
        assert stats.p99_ms >= 0


def teardown_module(module):
    date_str = datetime.now().strftime("%Y%m%d")
    file_name = f"test_report_{date_str}.json"

    # Load existing data if file exists
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # Ensure structure
    if "runs" not in existing_data:
        existing_data["runs"] = []

    # Append current run
    existing_data["runs"].append(TEST_REPORT)

    # Write back
    with open(file_name, "w") as f:
        json.dump(existing_data, f, indent=2, default=str)