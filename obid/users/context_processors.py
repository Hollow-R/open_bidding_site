from .models import Menu, GroupMenuPermission
from auctions.models import Auction, AuctionWinNotification


def user_menu_permissions(request):
    if request.user.is_authenticated:
        Auction.expire_overdue()
        # 1. Kullanıcının dahil olduğu grupları al
        user_groups = request.user.groups.all()
        
        # 2. Bu grupların yetkili olduğu menü ID'lerini bul
        allowed_menu_ids = GroupMenuPermission.objects.filter(
            group__in=user_groups,
            can_view=True
        ).values_list('menu_id', flat=True)
        
        # 3. Sadece yetkili olunan ve aktif menüleri getir
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

        win_notifications = list(
            AuctionWinNotification.objects.filter(user=request.user)
            .select_related('auction')
            .order_by('-created_at')[:12]
        )
        win_notifications_unread = AuctionWinNotification.objects.filter(
            user=request.user,
            read_at__isnull=True,
        ).count()

        return {
            'user_menus': menus,
            'user_menu_names': list(allowed_menu_names),
            'win_notifications': win_notifications,
            'win_notifications_unread': win_notifications_unread,
        }

    return {
        'user_menus': [],
        'user_menu_names': [],
        'win_notifications': [],
        'win_notifications_unread': 0,
    }