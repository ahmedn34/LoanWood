from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector
from django.db import connection
from .models import Item


@receiver(post_save, sender=Item)
def update_item_search_vector(sender, instance, **kwargs):
    """
    Updates PostgreSQL full-text search vector for an item upon save.
    Uses QuerySet.update() to prevent recursive signal triggers.
    """
    if connection.vendor == 'postgresql':
        Item.objects.filter(pk=instance.pk).update(
            search_vector=SearchVector('title', weight='A') + SearchVector('description', weight='B')
        )
