from django.db import migrations


def seed_watchlist_menu(apps, schema_editor):
    Menu = apps.get_model("users", "Menu")
    GroupMenuPermission = apps.get_model("users", "GroupMenuPermission")
    Group = apps.get_model("auth", "Group")

    menu, _ = Menu.objects.update_or_create(
        url_name="auctions:watchlist",
        defaults={
            "title": "İzlediklerim",
            "order": 22,
            "is_active": True,
        },
    )
    my_bids_menu = Menu.objects.filter(url_name="auctions:my_bids").first()
    if my_bids_menu:
        group_ids = (
            GroupMenuPermission.objects.filter(menu=my_bids_menu, can_view=True)
            .values_list("group_id", flat=True)
            .distinct()
        )
        for gid in group_ids:
            GroupMenuPermission.objects.get_or_create(
                group_id=gid,
                menu=menu,
                defaults={"can_view": True},
            )
    else:
        for g in Group.objects.all():
            GroupMenuPermission.objects.get_or_create(
                group=g,
                menu=menu,
                defaults={"can_view": True},
            )


def unseed_watchlist_menu(apps, schema_editor):
    Menu = apps.get_model("users", "Menu")
    Menu.objects.filter(url_name="auctions:watchlist").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_seed_auction_management_menu"),
    ]

    operations = [
        migrations.RunPython(seed_watchlist_menu, unseed_watchlist_menu),
    ]
