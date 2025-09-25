from prometheus_client import Counter, Gauge, Histogram


class UserMetrics:
    activities = Counter(
        "django_user_activities_total",
        "Total user activities",
        ["activity_type", "status"],
    )

    sessions = Gauge("django_active_user_sessions", "Currently active user sessions")


class ApprovalMetrics:
    operations = Counter(
        "django_approval_operations_total",
        "Total approval operations",
        ["operation_type", "status", "approval_type"],
    )

    processing_time = Histogram(
        "django_approval_processing_seconds",
        "Time spend processing approvals",
        ["approval_type", "status"],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
    )

    pending_approvals = Gauge(
        "django_pending_approvals_count",
        "Number of pending approvals",
    )


class HealthCheckMetrics:
    app_health = Gauge(
        "django_app_health_score", "Application health score", ["component"]
    )


class ErrorMetrics:
    error_counter = Counter(
        "django_errors_total",
        "Total application errors",
        ["error_type", "component", "severity"],
    )
