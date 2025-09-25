from datetime import time
from typing import Callable

import structlog
from django.http import HttpRequest, HttpResponse

from backend.apps.core.metrics.collectors import MetricsCollector

logger = structlog.get_logger(__name__)


class BusinessMetricsMiddleware:
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.start_time = time.time()

        try:
            response = self.get_response(request)
        except Exception as e:
            MetricsCollector.tracked_error(
                error_type=type(e).__name__,
                component=self._get_component_from_path(request.path),
                severity="error",
            )
            raise

        duration = time.time() - request.start_time

        if request.path.startswith("/approvals/"):
            if response.status_code >= 400:
                MetricsCollector.track_error(
                    error_tye="http_error",
                    component="approvals",
                    severity="warning" if response.status_code >= 500 else "error",
                )
        elif request.path.startswith("/users/"):
            if response.status_code >= 400:
                MetricsCollector.track_error(
                    error_type="http_error",
                    component="users",
                    severity="warning" if response.status_code >= 500 else "error",
                )

        return response

    def _get_component_from_path(self, path: str) -> str:
        if path.startswith("/users"):
            return "users"
        elif path.startswith("/approvals/"):
            return "approvals"
        elif path.startswith("/admin/"):
            return "admin"
        return "unknown"
