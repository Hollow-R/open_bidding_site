from django.shortcuts import redirect
from django.contrib import messages
from .models import GroupMenuPermission

def menu_permission_required(url_name):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # 1. Giriş yapmamışsa login'e at
            if not request.user.is_authenticated:
                return redirect('users:login')
            
            # 2. Kullanıcının gruplarının bu URL'ye yetkisi var mı?
            user_groups = request.user.groups.all()
            has_permission = GroupMenuPermission.objects.filter(
                group__in=user_groups,
                menu__url_name=url_name,
                can_view=True
            ).exists()

            # 3. Yetki varsa devam et, yoksa ana sayfaya at ve uyarı ver
            if has_permission or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
                return redirect('users:dashboard')
        return _wrapped_view
    return decorator