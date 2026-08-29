from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

CONDITION_CHOICES = [
    ('excellent', 'Excellent'),
    ('good', 'Good'),
    ('fair', 'Fair'),
    ('worn', 'Worn'),
]


class Category(models.Model):
    """Category taxonomy for equipment and tools."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Item(models.Model):
    """Tool or equipment item available for community lending."""
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='items'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='items'
    )
    title = models.CharField(max_length=120)
    description = models.TextField()
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='good'
    )
    photo = models.ImageField(upload_to='items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    search_vector = SearchVectorField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_vector']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def currently_borrowed(self):
        """Returns True if there is an active or approved borrow request for this item."""
        return self.requests.filter(status__in=['active', 'approved']).exists()
