import abc
from typing import Dict, Any, Optional

class BaseMetricsExporter(abc.ABC):
    """
    Abstract interface for exporting metrics to external platforms (e.g. OpenTelemetry, Prometheus).
    """
    @abc.abstractmethod
    def export_counter(self, name: str, value: int, tags: Optional[Dict[str, str]] = None) -> None:
        """Increments a counter metric."""
        pass

    @abc.abstractmethod
    def export_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Sets the current value of a gauge metric."""
        pass

    @abc.abstractmethod
    def export_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Records a value in a histogram/distribution metric."""
        pass


class OTelMetricsExporterPlaceholder(BaseMetricsExporter):
    """
    Placeholder/No-Op exporter for OpenTelemetry to allow future integrations
    without modifying the core monitoring code.
    """
    def export_counter(self, name: str, value: int, tags: Optional[Dict[str, str]] = None) -> None:
        # Placeholder: could forward to otel counter in future
        pass

    def export_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        # Placeholder: could forward to otel gauge in future
        pass

    def export_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        # Placeholder: could forward to otel histogram/summary in future
        pass


class MetricsRegistry:
    """
    Ecosystem in-memory metrics registry. Collects counts, latencies, and db operations.
    """
    def __init__(self, exporter: Optional[BaseMetricsExporter] = None):
        self.exporter = exporter or OTelMetricsExporterPlaceholder()
        
        # In-memory metrics stores
        self.total_requests = 0
        self.error_count = 0
        self.auth_failures = 0
        self.db_queries = 0
        self.redis_operations = 0
        self.total_response_time = 0.0

    def increment_request(self) -> None:
        self.total_requests += 1
        self.exporter.export_counter("http_requests_total", 1)

    def record_response_time(self, duration_ms: float) -> None:
        self.total_response_time += duration_ms
        self.exporter.export_histogram("http_request_duration_ms", duration_ms)

    def increment_error(self) -> None:
        self.error_count += 1
        self.exporter.export_counter("http_errors_total", 1)

    def increment_auth_failure(self) -> None:
        self.auth_failures += 1
        self.exporter.export_counter("auth_failures_total", 1)

    def increment_db_query(self) -> None:
        self.db_queries += 1
        self.exporter.export_counter("db_queries_total", 1)

    def increment_redis_op(self) -> None:
        self.redis_operations += 1
        self.exporter.export_counter("redis_operations_total", 1)

    def get_average_response_time(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests

    def reset(self) -> None:
        """Resets all metrics (useful for testing)."""
        self.total_requests = 0
        self.error_count = 0
        self.auth_failures = 0
        self.db_queries = 0
        self.redis_operations = 0
        self.total_response_time = 0.0

# Global Metrics Registry instance
metrics_registry = MetricsRegistry()
