from .models import Menu, GroupMenuPermission

def user_menu_permissions(request):
    if request.user.is_authenticated:
        # 1. Kullanıcının dahil olduğu grupları al
        user_groups = request.user.groups.all()
        
        # 2. Bu grupların yetkili olduğu menü ID'lerini bul
        allowed_menu_ids = GroupMenuPermission.objects.filter(
            group__in=user_groups,
            can_view=True
        ).values_list('menu_id', flat=True)
        
        # 3. Sadece yetkili olunan ve aktif menüleri getir (Sıralı halde)
        menus = Menu.objects.filter(
            id__in=allowed_menu_ids,
            is_active=True,
            parent_menu__isnull=True # Ana menüler
        ).distinct().order_by('order')
        
        # Aynı zamanda izin verilen menu url_name değerlerini template'e ver
        allowed_menu_names = GroupMenuPermission.objects.filter(
            group__in=user_groups,
            can_view=True
        ).values_list('menu__url_name', flat=True)

        return {
            'user_menus': menus,
            'user_menu_names': list(allowed_menu_names)
        }
    
    return {'user_menus': []}