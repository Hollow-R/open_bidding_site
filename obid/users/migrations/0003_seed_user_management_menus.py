from django.db import migrations


def create_user_management_menus(apps, schema_editor):
    Menu = apps.get_model("users", "Menu")

    Menu.objects.update_or_create(
        url_name="users:user_management",
        defaults={
            "title": "Kullanıcı Yönetimi",
            "order": 50,
            "is_active": True,
        },
    )
    Menu.objects.update_or_create(
        url_name="users:group_permissions",
        defaults={
            "title": "Grup Menü Yetkileri",
            "order": 60,
            "is_active": True,
        },
    )


def remove_user_management_menus(apps, schema_editor):
    Menu = apps.get_model("users", "Menu")
    Menu.objects.filter(
        url_name__in=["users:user_management", "users:group_permissions"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_groupmenupermission_can_view"),
    ]

    operations = [
        migrations.RunPython(
            create_user_management_menus,
            reverse_code=remove_user_management_menus,
        ),
    ]
