from django.db import migrations


def create_auction_management_menu(apps, schema_editor):
    Menu = apps.get_model("users", "Menu")
    Menu.objects.update_or_create(
        url_name="auctions:management",
        defaults={
            "title": "İhale Yönetimi İşlemleri",
            "order": 25,
            "is_active": True,
        },
    )


def remove_auction_management_menu(apps, schema_editor):
    Menu = apps.get_model("users", "Menu")
    Menu.objects.filter(url_name="auctions:management").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_seed_system_panel_menu"),
    ]

    operations = [
        migrations.RunPython(
            create_auction_management_menu,
            reverse_code=remove_auction_management_menu,
        ),
    ]
