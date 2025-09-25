from django.shortcuts import redirect, render
import logging

logger = logging.getLogger(__name__)

def index(request):
    if request.user.is_authenticated:
        return redirect("approvals:")
    return redirect("users:login")

def handler400(request, exception):
    logger.warning(f"400: {request.path}")
    return render(request, '400.html', status=400)

def handler403(request, exception):
    logger.warning(f"403: {request.path} from {request.META.get('REMOTE_ADDR')}")
    return render(request, '403.html', status=403)

def csrf_failure_view(request, reason=""):
    """CSRF 검증 실패 시 호출되는 뷰"""
    return render(request, 'csrf_error.html', status=403)

def handler404(request, exception):
    logger.error(f"404: {request.path}")
    return render(request, '404.html', status=404)

def handler500(request):
    logger.critical("500 error occurred", exc_info=True)
    return render(request, '500.html', status=500)