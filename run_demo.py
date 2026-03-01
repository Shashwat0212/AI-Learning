import time

from askmydocs.core.config import SLAConfig, TracingConfig
from askmydocs.core.tracing.stats import StatsAggregator
from askmydocs.core.tracing.sla import SLARegistry
from askmydocs.core.tracing.tracer import Tracer
from askmydocs.core.types import StageSLA
from askmydocs.core.tracing.exporter import JSONExporter

def print_trace(trace_record):
    print(f"\nTrace: {trace_record.request_id}")
    print(f"Total duration: {trace_record.total_duration_ns / 1_000_000:.3f} ms")

    for span in trace_record.steps:
        indent = "  " if span.parent_span_id else ""
        print(
            f"{indent}- {span.stage_name}: "
            f"{span.duration_ns / 1_000_000:.3f} ms"
        )


def print_report(report):
    print("\nStage Stats:")
    for stage, stats in report.stages.items():
        print(
            f"{stage} → count={stats.count}, "
            f"p50={stats.p50_ms:.3f}ms, "
            f"p95={stats.p95_ms:.3f}ms, "
            f"p99={stats.p99_ms:.3f}ms"
        )


def main():
    agg = StatsAggregator(window_size=5000)

    budgets = {
        "retrieve": StageSLA(max_p95_ms=10.0),
    }

    sla = SLARegistry(SLAConfig(stage_budgets=budgets, fail_fast=False))

    exporter = JSONExporter(trace_path="demo_trace.jsonl", metrics_path="demo_metrics.json")
    
    tracer = Tracer(
        TracingConfig(enable_tracing=True),
        aggregator=agg,
        sla_registry=sla,
        exporter=exporter,
    )

    with tracer.request("demo-request") as trace:
        with trace.span("retrieve"):
            time.sleep(0.003)

        with trace.span("rerank"):
            time.sleep(0.002)

    report = agg.report()
    print_report(report)


if __name__ == "__main__":
    main()