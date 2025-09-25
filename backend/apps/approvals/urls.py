from django.urls import path

from backend.apps.approvals.views import (
    approval_action,
    approvals_view,
    external_url_test,
)

app_name = "approvals"
urlpatterns = [
    path("", approvals_view, name=""),
    path("approval_action/", approval_action, name="approvals_action"),
    path("external", external_url_test, name="external_url"),
]
