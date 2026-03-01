import json
from typing import Any, Dict

from ..types import TraceRecord, Report


class JSONExporter:
    """
    Responsible for exporting structured tracing data.

    Files:
    - trace.jsonl  → append-only per request
    - metrics.json → rolling snapshot
    """

    def __init__(
        self,
        trace_path: str = "trace.jsonl",
        metrics_path: str = "metrics.json",
    ):
        self._trace_path = trace_path
        self._metrics_path = metrics_path

    # ----------------------------
    # Public API
    # ----------------------------

    def export_trace(self, trace: TraceRecord) -> None:
        record = self._serialize_trace(trace)

        with open(self._trace_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def export_report(self, report: Report) -> None:
        record = self._serialize_report(report)

        with open(self._metrics_path, "w") as f:
            json.dump(record, f, indent=2)

    # ----------------------------
    # Serialization helpers
    # ----------------------------

    def _serialize_trace(self, trace: TraceRecord) -> Dict[str, Any]:
        return {
            "request_id": trace.request_id,
            "started_at_ns": trace.started_at_ns,
            "ended_at_ns": trace.ended_at_ns,
            "total_duration_ms": trace.total_duration_ns / 1_000_000,
            "metadata": trace.metadata,
            "spans": [
                {
                    "stage_name": span.stage_name,
                    "duration_ms": span.duration_ns / 1_000_000,
                    "started_at_ns": span.started_at_ns,
                    "ended_at_ns": span.ended_at_ns,
                    "metadata": span.metadata,
                    "span_id": span.span_id,
                    "parent_span_id": span.parent_span_id,
                }
                for span in trace.steps
            ],
        }

    def _serialize_report(self, report: Report) -> Dict[str, Any]:
        return {
            "generated_at_ns": report.generated_at_ns,
            "stages": {
                stage: {
                    "count": stats.count,
                    "p50_ms": stats.p50_ms,
                    "p95_ms": stats.p95_ms,
                    "p99_ms": stats.p99_ms,
                }
                for stage, stats in report.stages.items()
            },
        }