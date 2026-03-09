# Base error for all performance system errors
class PerformanceError(Exception):
    """Base class for performance instrumentation errors."""


# ----------------------------
# Tracing / Measurement Errors
# ----------------------------

class TracingError(PerformanceError):
    """Errors related to span/trace lifecycle misuse."""


class InvalidSpanError(TracingError):
    """Raised when a span has invalid timing or structure."""


class SpanHierarchyError(TracingError):
    """Raised when parent/child span relationships are invalid."""


# ----------------------------
# SLA Errors
# ----------------------------

class SLAViolationError(PerformanceError):
    """
    Raised when a stage exceeds configured SLA budgets.

    Should contain stage name and violation details.
    """

    def __init__(self, stage_name: str, metric: str, observed_value: float):
        self.stage_name = stage_name
        self.metric = metric
        self.observed_value = observed_value

        super().__init__(
            f"SLA violation in stage '{stage_name}': "
            f"{metric} = {observed_value}"
        )


# ----------------------------
# Configuration Errors
# ----------------------------

class ConfigurationError(PerformanceError):
    """Raised when tracing or SLA configuration is invalid."""


# ----------------------------
# Ingestion Errors
# ----------------------------

class DocumentTooLargeError(PerformanceError):
    """
    Raised when a file exceeds the configured MAX_DOCUMENT_SIZE_MB limit
    during ingestion.

    This prevents extremely large files from being processed by the
    ingestion pipeline.
    """

    def __init__(self, file_path: str, max_size_mb: int):
        self.file_path = file_path
        self.max_size_mb = max_size_mb

        super().__init__(
            f"Document '{file_path}' exceeds maximum allowed size of {max_size_mb} MB"
        )