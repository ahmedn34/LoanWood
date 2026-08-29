from django.db import models
from django.db.models import Q, F, CheckConstraint
from django.contrib.auth.models import User
from django.utils import timezone
from items.models import Item, CONDITION_CHOICES

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('declined', 'Declined'),
    ('cancelled', 'Cancelled'),
    ('active', 'Active'),
    ('returned', 'Returned'),
    ('overdue', 'Overdue'),
]


class BorrowRequest(models.Model):
    """Borrow request and rental transaction between community members."""
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='requests'
    )
    borrower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='borrow_requests'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    message = models.TextField(blank=True, default='')
    decline_reason = models.TextField(blank=True, default='')
    returned_at = models.DateTimeField(null=True, blank=True)
    return_condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        null=True,
        blank=True
    )
    return_note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            CheckConstraint(
                condition=Q(end_date__gte=F('start_date')),
                name='end_after_start'
            )
        ]

    def __str__(self):
        return f"{self.borrower.username} -> {self.item.title} ({self.get_status_display()})"

    def is_overdue(self):
        """Returns True if the loan is currently active and past its scheduled end date."""
        return self.status == 'active' and self.end_date < timezone.now().date()


class Notification(models.Model):
    """Community notification for lending, borrowing, and return events."""
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.CharField(max_length=200)
    link = models.CharField(max_length=200, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:30]}"
