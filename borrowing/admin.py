from django.contrib import admin
from .models import BorrowRequest, Notification


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = (
        'item',
        'borrower',
        'start_date',
        'end_date',
        'status',
        'is_overdue_status',
        'return_condition',
        'returned_at',
        'created_at',
    )
    list_filter = ('status', 'return_condition', 'start_date', 'end_date', 'created_at')
    search_fields = ('item__title', 'borrower__username', 'borrower__email', 'message', 'decline_reason', 'return_note')
    readonly_fields = ('created_at',)

    @admin.display(boolean=True, description='Overdue')
    def is_overdue_status(self, obj):
        return obj.is_overdue()


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'link', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__username', 'recipient__email', 'message', 'link')
    readonly_fields = ('created_at',)
