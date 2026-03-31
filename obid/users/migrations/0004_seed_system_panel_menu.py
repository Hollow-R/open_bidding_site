from django.db import migrations


def create_system_panel_menu(apps, schema_editor):
    Menu = apps.get_model("users", "Menu")

    Menu.objects.update_or_create(
        url_name="users:admin_dashboard",
        defaults={
            "title": "Sistem Paneli",
            "order": 10,
            "is_active": True,
        },
    )
    Menu.objects.update_or_create(
        url_name="auctions:list",
        defaults={
            "title": "İhale Yönetimi",
            "order": 20,
            "is_active": True,
        },
    )


def remove_system_panel_menu(apps, schema_editor):
    Menu = apps.get_model("users", "Menu")
    Menu.objects.filter(url_name="users:admin_dashboard").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_seed_user_management_menus"),
    ]

    operations = [
        migrations.RunPython(
            create_system_panel_menu,
            reverse_code=remove_system_panel_menu,
        ),
    ]
