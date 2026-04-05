from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.shortcuts import redirect

from .models import GroupMenuPermission

PERMISSION_DENIED_MSG = "Bu sayfaya erişim yetkiniz bulunmamaktadır."


def user_has_menu_permission(user, menu_url_name):
    if not user.is_authenticated:
        return False
    return GroupMenuPermission.objects.filter(
        group__in=user.groups.all(),
        menu__url_name=menu_url_name,
        can_view=True,
    ).exists()


def _respond_permission_denied(request):
    if (
        request.path.startswith("/api/")
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or (request.content_type and "application/json" in request.content_type)
    ):
        return JsonResponse({"success": False, "error": PERMISSION_DENIED_MSG}, status=403)
    messages.error(request, PERMISSION_DENIED_MSG)
    return redirect("users:dashboard")


def menu_permission_required(menu_url_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not user_has_menu_permission(request.user, menu_url_name):
                return _respond_permission_denied(request)
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
