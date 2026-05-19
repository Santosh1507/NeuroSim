"""Lightweight monitoring and observability for NeuroSim API."""
import time
from typing import Dict, List


class MetricsCollector:
    """In-memory metrics collector for API monitoring."""

    def __init__(self):
        self._request_counts: Dict[str, int] = {}
        self._error_counts: Dict[str, int] = {}
        self._response_times: Dict[str, List[float]] = {}
        self._start_time = time.time()

    def record_request(self, method: str, path: str, status: int, duration_ms: float):
        key = f"{method} {path}"
        self._request_counts[key] = self._request_counts.get(key, 0) + 1
        if status >= 500:
            self._error_counts[key] = self._error_counts.get(key, 0) + 1
        if key not in self._response_times:
            self._response_times[key] = []
        self._response_times[key].append(duration_ms)
        if len(self._response_times[key]) > 100:
            self._response_times[key] = self._response_times[key][-100:]

    def get_summary(self) -> dict:
        uptime = time.time() - self._start_time
        total_requests = sum(self._request_counts.values())
        total_errors = sum(self._error_counts.values())
        avg_times = {}
        for key, times in self._response_times.items():
            if times:
                avg_times[key] = round(sum(times) / len(times), 2)
        return {
            "uptime_seconds": round(uptime, 0),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(total_errors / max(total_requests, 1), 4),
            "avg_response_times_ms": avg_times,
            "top_endpoints": sorted(self._request_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    def reset(self):
        self._request_counts.clear()
        self._error_counts.clear()
        self._response_times.clear()


metrics = MetricsCollector()
