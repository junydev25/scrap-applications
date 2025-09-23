from functools import wraps

from django.shortcuts import redirect


def require_authentication(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("users:login")
        return view_func(request, *args, **kwargs)

    return wrapper
