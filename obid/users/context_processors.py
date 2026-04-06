from .models import Menu, GroupMenuPermission
from auctions.models import Auction, AuctionWinNotification


def user_menu_permissions(request):
    if request.user.is_authenticated:
        # 1. Kullanıcının dahil olduğu grupları al
        user_groups = request.user.groups.all()

        permissions = list(
            GroupMenuPermission.objects.filter(
                group__in=user_groups,
                can_view=True
            ).select_related('menu')
        )
        allowed_menu_ids = [perm.menu_id for perm in permissions]
        allowed_menu_names = [perm.menu.url_name for perm in permissions]

        # 2. Sadece yetkili olunan ve aktif menüleri getir
        menus = Menu.objects.filter(
            id__in=allowed_menu_ids,
            is_active=True,
            parent_menu__isnull=True # Ana menüler
        ).distinct().order_by('order')

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