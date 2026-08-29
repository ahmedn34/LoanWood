from django.apps import AppConfig


class ItemsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'items'
    verbose_name = 'Tool & Equipment Inventory'

    def ready(self):
        import items.signals  # noqa: F401
