from django.contrib import messages
from django.test import TestCase
from django.urls import reverse

from backend.apps.users.models import User


# Create your tests here.
class UserTest(TestCase):
    def setUp(self):
        self.login_url = reverse("users:login")
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
        )

    def test_login_get_request(self):
        """GET 요청으로 로그인 페이지 접근 테스트"""
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "testpass",
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("approvals:"))

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "testuser")

    def test_login_failure_wrong_password(self):
        response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "wrongpass",
        })

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "로그인에 실패했습니다. 다시 로그인해주세요.")

        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_failure_empty_fields(self):
        """빈 필드로 로그인 실패 테스트"""
        response = self.client.post(self.login_url, {
            "username": "",
            "password": ""
        })

        # 폼 에러가 있는지 확인
        self.assertContains(response, "form")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_already_authenticated_user_redirect(self):
        """이미 로그인된 사용자 리다이렉트 테스트"""
        self.client.login(username="testuser", password="testpass")

        response = self.client.get(self.login_url)

        # approvals 페이지로 리다이렉트되어야 함
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("approvals:"))

