from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from backend.apps.core.metrics.collectors import MetricsCollector
from backend.apps.users.forms import LoginForm


# Create your views here.
def login_view(request):
    if request.user.is_authenticated:
        return redirect("approvals:")

    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(username=username, password=password)
            if user:
                login(request, user)

                MetricsCollector.track_user_activity("login", "success")
                return redirect("approvals:")
        messages.error(request, "로그인에 실패했습니다. 다시 로그인해주세요.")

    MetricsCollector.track_error("user_login_failed", "users")

    context = {"form": form}

    return render(request, "users/login.html", context)


def logout_view(request):
    logout(request)
    return redirect("users:login")
