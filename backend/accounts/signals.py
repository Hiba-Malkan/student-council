from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from notifications.models import NotificationPreference


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences for new users"""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)