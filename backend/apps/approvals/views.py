import json
import time
from typing import Any, Dict, Optional

import requests
import structlog
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.forms import model_to_dict
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from backend.apps.approvals.models import Approval
from backend.apps.core.decorators import require_authentication
from backend.apps.core.metrics.collectors import MetricsCollector
from backend.apps.users.models import User

logger = structlog.get_logger(__name__)


class ApprovalService:
    """
    승인 관련 비즈니스 로직을 담당한느 서비스 클래스
    """

    VALID_ACTIONS = {
        "approved": {"status": "approved"},
        "rejected": {"status": "rejected"},
    }

    def __init__(self):
        self.properties = settings.APPROVALS_PROPERTIES
        self.external_url = self.properties["EXTERNAL_URL"]
        self.order_by_ = (
            f"{'' if self.properties['ORDER_BY'] != 'DESC' else '-'}submitted_at"
        )

    def get_pending_approvals(self, approved_by: User) -> list:
        return (
            Approval.objects.filter(approved_by=approved_by, status="pending")
            .select_related("applicant")
            .order_by(self.order_by_)
            .values(
                "id",
                "title",
                "applicant__username",
                "content",
                "status",
                "submitted_at",
            )
        )

    def get_approval_by_id(self, approval_id: int) -> Optional[Approval]:
        return get_object_or_404(Approval, pk=approval_id)

    def validate_current_user_permission(
        self, approval: Approval, current_user: User
    ) -> bool:
        if approval.approved_by != current_user:
            raise PermissionDenied("해당 신청 내역을 승인 또는 거부할 권한이 없습니다.")

    def validate_action(self, action: str) -> None:
        if action not in self.VALID_ACTIONS:
            raise ValueError("잘못된 요청입니다.")

    @transaction.atomic
    def process_approval(self, approval: Approval, action: str) -> None:
        old_status = approval.status

        approval.status = self.VALID_ACTIONS[action]["status"]
        approval.processed_at = timezone.now()
        approval.save()

        logger.debug(
            f"Approval 상태가 변경되었습니다.({old_status} -> {approval.status})"
        )

    def serialize_approval_for_external_api(self, approval: Approval) -> Dict[str, Any]:
        approval_dict = model_to_dict(approval)

        for key, value in approval_dict.items():
            if hasattr(value, "isoformat"):
                approval_dict[key] = value.isoformat()

        return approval_dict

    def send_to_external_api(self, approval_data: Dict[str, Any]) -> requests.Response:
        try:
            return requests.post(self.external_url, json=approval_data, timeout=30)
        except requests.RequestException as e:
            logger.error(f"External API 호출 실패: {e}")
            raise


@require_authentication
def approvals_view(request: HttpRequest) -> HttpResponse:
    service = ApprovalService()
    per_page = service.properties["ITEMS_PER_PAGE"]

    approvals_list = service.get_pending_approvals(request.user)

    paginator = Paginator(approvals_list, per_page)
    page = int(request.GET.get("page", 1))
    page_obj = paginator.get_page(page)

    approval_id = request.GET.get("approval_id")
    selected_approval = None
    if approval_id is not None:
        try:
            selected_approval = service.get_approval_by_id(approval_id)
        except Http404:
            logger.error("이미 승인/거부 되었거나 존재하지 않는 신청 내역을 요청")
            messages.error(
                request, "이미 승인/거부 되었거나 존재하지 않는 신청 내역입니다."
            )

    context = {
        "page_obj": page_obj,
        "approvals": page_obj.object_list,
        "selected_approval": selected_approval,
    }

    return render(request, "approvals/approvals.html", context)


@require_POST
@require_authentication
def approval_action(request: HttpRequest) -> HttpResponse:
    service = ApprovalService()

    approval_id = request.POST.get("approval_id")
    action = request.POST.get("action")

    if not approval_id or not action:
        messages.error(request, "필수 파라미터가 누락되었습니다.")
        return redirect("approvals:")

    start_time = time.time()
    try:
        approval = service.get_approval_by_id(approval_id)

        service.validate_current_user_permission(approval, request.user)
        service.validate_action(action)

        service.process_approval(approval, action)

        approval_data = service.serialize_approval_for_external_api(approval)
        response = service.send_to_external_api(approval_data)

        if response.status_code == 200:
            message = response.json().get("message", "처리")
            messages.success(request, f"{message} 성공")
            logger.debug("외부 API로 approval data 전송 성공")
        else:
            messages.error(request, "요청에 실패했습니다.")

        duration = time.time() - start_time
        MetricsCollector.track_approval_operation(
            "process", type(approval), "success", duration
        )

    except (PermissionDenied, ValueError, requests.RequestException, Exception) as e:
        MetricsCollector.track_approval_operation(
            "process", type(approval), "fail", time.time() - start_time
        )
        MetricsCollector.track_error("approval_processing_failed", "approvals")

        if isinstance(e, PermissionDenied):
            return HttpResponseForbidden(str(e))
        elif isinstance(e, ValueError):
            return HttpResponseBadRequest(str(e))
        elif isinstance(e, requests.RequestException):
            logger.error(f"처리 중 오류 발생: {e}")
            return HttpResponseServerError("외부 서비스 오류가 발생했습니다.")
        else:
            logger.error(f"처리 중 오류 발생: {e}")
            return HttpResponseServerError("서버 오류가 발생했습니다.")

    return redirect("approvals:")


@require_POST
@csrf_exempt
def external_url_test(request: HttpRequest) -> JsonResponse:
    """테스트용 외부 URL 엔드포인트 (추후 삭제 예정)"""
    try:
        data = json.loads(request.body)
        status = data.get("status")

        status_messages = {"approved": "승인", "rejected": "거부"}

        if status in status_messages:
            return JsonResponse({"message": status_messages[status]})
        else:
            return HttpResponseForbidden("잘못된 요청입니다.")

    except json.JSONDecodeError:
        return HttpResponseBadRequest("잘못된 JSON 형식입니다.")
    except Exception as e:
        logger.error(f"External URL test 처리 중 오류: {e}")
        return HttpResponseServerError("서버 오류가 발생했습니다.")
