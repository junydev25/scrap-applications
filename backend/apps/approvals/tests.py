from unittest.mock import Mock, patch

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.db.models import Max
from django.http import Http404
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from backend.apps.approvals.models import Approval
from backend.apps.approvals.views import ApprovalService

# Create your tests here.
User = get_user_model()


class ApprovalServiceTest(TestCase):
    def setUp(self):
        self.service = ApprovalService()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
        )
        self.applicant = User.objects.create_user(
            username="applicant",
            password="testpass",
        )
        self.approval = Approval.objects.create(
            title="Test Approval",
            content="Test Content",
            applicant=self.applicant,
            approved_by=self.user,
            status="pending",
            submitted_at=timezone.now(),
        )

    def test_get_pending_approvals(self):
        approvals = self.service.get_pending_approvals(self.user)
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0]["title"], "Test Approval")

    def test_get_pending_approvals_from_invalid_user(self):
        user_max_id = User.objects.aggregate(Max("id"))["id__max"]
        invalid_user = User(id=user_max_id + 1, username="invalid_user")
        approvals = self.service.get_pending_approvals(invalid_user)
        self.assertEqual(len(approvals), 0)

    def test_get_approval_by_id(self):
        approval = self.service.get_approval_by_id(self.approval.id)
        self.assertEqual(approval, self.approval)

    def test_get_approval_by_invalid_id(self):
        approval_max_id = Approval.objects.aggregate(Max("id"))["id__max"]
        with self.assertRaises(Http404):
            self.service.get_approval_by_id(approval_max_id + 1)

    def test_validate_user_permission_valid(self):
        self.service.validate_current_user_permission(self.approval, self.user)

    def test_validate_user_permission_invalid(self):
        invalid_user = User.objects.create_user(
            username="invalid_user", password="invalid_pass"
        )

        with self.assertRaises(PermissionDenied):
            self.service.validate_current_user_permission(self.approval, invalid_user)

    def test_validate_action_valid(self):
        self.service.validate_action("approved")
        self.service.validate_action("rejected")

    def test_validate_action_invalid(self):
        with self.assertRaises(ValueError):
            self.service.validate_action("invalid_action")

    def test_process_approval(self):
        self.service.process_approval(self.approval, "approved")
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, "approved")
        self.assertIsNotNone(self.approval.processed_at)

    @patch.object(Approval, "save")
    def test_process_approval_failure(self, mock_save):
        mock_save.side_effect = DatabaseError("Connection error")

        with self.assertRaises(DatabaseError):
            self.service.process_approval(self.approval, "approved")

        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, "pending")
        self.assertIsNone(self.approval.processed_at)

    def test_serialize_approval_for_external_api(self):
        self.approval.processed_at = timezone.now()
        self.approval.save()

        serialized = self.service.serialize_approval_for_external_api(self.approval)

        self.assertIn("id", serialized)
        self.assertIn("title", serialized)
        self.assertIn("status", serialized)

        self.assertIsInstance(serialized["submitted_at"], str)

    @patch("requests.post")
    def test_send_to_external_api_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        data = {"test", "data"}
        response = self.service.send_to_external_api(data)

        self.assertEqual(response.status_code, 200)
        mock_post.assert_called_once_with(
            self.service.external_url,
            json=data,
            timeout=30,
        )

    @patch("requests.post")
    def test_send_to_external_api_failure(self, mock_post):
        mock_post.side_effect = requests.RequestException("Connectioin error")

        data = {"test": "data"}

        with self.assertRaises(requests.RequestException):
            self.service.send_to_external_api(data)


class ApprovalViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.applicant = User.objects.create_user(
            username="applicant", password="testpass"
        )
        self.approval = Approval.objects.create(
            title="Test Approval",
            content="Test content",
            applicant=self.applicant,
            approved_by=self.user,
            status="pending",
            submitted_at=timezone.now(),
        )

        if not hasattr(settings, "APPROVALS_PROPERTIES"):
            settings.APPROVALS_PROPERTIES = {
                "ITEMS_PER_PAGE": 10,
                "EXTERNAL_URL": "http://test-external-api.com",
            }

    @patch("backend.apps.approvals.views.ApprovalService.send_to_external_api")
    def test_full_approval_workflow(self, mock_send):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "승인"}
        mock_send.return_value = mock_response

        approval = Approval.objects.create(
            title="Test Approval",
            content="Test Content",
            applicant=self.applicant,
            approved_by=self.user,
            status="pending",
            submitted_at=timezone.now(),
        )

        # 로그인
        self.client.login(username="testuser", password="testpass")

        # 신청내역들 확인 - 승인/거부 필요
        response = self.client.get(reverse("approvals:"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Approval")

        # 특정 신청내역 - 승인 처리
        response = self.client.post(
            reverse("approvals:approvals_action"),
            {
                "approval_id": approval.id,
                "action": "approved",
            },
        )
        self.assertRedirects(response, reverse("approvals:"))

        # 결과 확인
        approval.refresh_from_db()
        self.assertEqual(approval.status, "approved")
        self.assertIsNotNone(approval.processed_at)

        # External API 호출 확인
        mock_send.assert_called_once()
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("승인 성공" in str(m) for m in messages))
