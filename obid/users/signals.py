from django.contrib.auth.models import Group, User
from django.db.models.signals import post_save
from django.dispatch import receiver


def _assign_customer_group(user: User) -> None:
    if user.groups.exists():
        return
    customer_group, _ = Group.objects.get_or_create(name="Müşteri")
    user.groups.add(customer_group)


@receiver(post_save, sender=User)
def assign_customer_group_on_create(sender, instance, created, **kwargs):
    if created:
        _assign_customer_group(instance)
