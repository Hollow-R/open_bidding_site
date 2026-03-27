from django.contrib import admin
from .models import Menu, GroupMenuPermission

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('title', 'url_name', 'parent_menu', 'order', 'is_active')
    list_editable = ('order', 'is_active') # Listeden hızlıca düzenlemek için

admin.site.register(GroupMenuPermission)