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