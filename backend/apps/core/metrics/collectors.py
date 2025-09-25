from typing import Any, Optional

from django.contrib.auth import user_logged_in, user_logged_out
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.apps.approvals.models import Approval
from backend.apps.core.metrics.core import ApprovalMetrics, ErrorMetrics, UserMetrics
from backend.apps.users.models import User


class MetricsCollector:
    @staticmethod
    def track_user_activity(
        activity_type: str, status: str = "success", user_id: Optional[int] = None
    ) -> None:
        UserMetrics.activities.labels(
            activity_type=activity_type,
            status=status,
        ).inc()

    @staticmethod
    def track_approval_operation(
        operation_type: str,
        approval_type: str,
        status: str = "success",
        duration: Optional[float] = None,
    ) -> None:
        ApprovalMetrics.operations.labels(
            operation_type=operation_type,
            approval_type=approval_type,
            status=status,
        ).inc()

        if duration is not None:
            ApprovalMetrics.processing_time.labels(
                approval_type=approval_type,
                status=status,
            )

    @staticmethod
    def update_pending_approvals_count() -> None:
        from backend.apps.approvals.models import Approval

        count = Approval.objects.filter(status="pending").count()

        ApprovalMetrics.pending_approvals.set(count)

    @staticmethod
    def track_error(
        error_type: str,
        component: str,
        severity: str = "error",
        exception: Optional[Exception] = None,
    ) -> None:
        ErrorMetrics.error_counter.labels(
            error_type=error_type,
            component=component,
            severity=severity,
        ).inc()


@receiver(user_logged_in)
def on_user_login(sender: Any, user: User, request: Any, **kwargs: Any) -> None:
    MetricsCollector.track_user_activity("login", "success", user.id)


@receiver(user_logged_out)
def on_user_logout(sender: Any, user: User, request: Any, **kwargs: Any) -> None:
    MetricsCollector.track_user_activity("logout", "success", user.id)


@receiver([post_save, post_delete], sender="approvals.Approval")
def on_approval_change(sender: Approval, **kwargs: Any) -> None:
    MetricsCollector.update_pending_approvals_count()
