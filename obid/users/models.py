from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

class Menu(models.Model):
    title = models.CharField(max_length=100, verbose_name="Menu name")
    url_name = models.CharField(max_length=100, help_text="'name' parameter in urls.py (auctions:list)")
    parent_menu = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='submenus',
        verbose_name="Üst Menü"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Sıralama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")

    class Meta:
        ordering = ['order']
        verbose_name = "Menü"
        verbose_name_plural = "Menüler"

    def __str__(self):
        return self.title
    
class GroupMenuPermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="menu_permissions")
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="group_permissions")
    can_view = models.BooleanField(default=True)

    class Meta:
        unique_together = ('group', 'menu')
        verbose_name = "Grup Menü Yetkisi"
        verbose_name_plural = "Grup Menü Yetkileri"

    def __str__(self):
        return f"{self.group.name} -> {self.menu.title}"