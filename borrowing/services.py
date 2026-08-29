from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from items.models import Item
from .models import BorrowRequest, Notification


def sync_overdue_statuses():
    """
    Scans all currently active borrow requests and updates those past their end date to overdue.
    Returns the count of updated records.
    """
    today = timezone.now().date()
    return BorrowRequest.objects.filter(
        status='active',
        end_date__lt=today
    ).update(status='overdue')


def overlapping_requests(item, start_date, end_date, exclude_id=None):
    """
    Queries borrow requests for a specific item that overlap with [start_date, end_date]
    and are in 'approved' or 'active' status.
    """
    qs = BorrowRequest.objects.filter(
        item=item,
        status__in=['approved', 'active'],
        start_date__lte=end_date,
        end_date__gte=start_date
    )
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    return qs


def approve_request(request_obj):
    """
    Approves a borrow request with transactional row locking and automatic resolution
    of overlapping pending requests.
    """
    with transaction.atomic():
        # Lock item row to prevent concurrent approvals for the same item
        item = Item.objects.select_for_update().get(id=request_obj.item_id)

        # Query all other pending requests for the same item with overlapping dates
        overlapping_pending = BorrowRequest.objects.select_for_update().filter(
            item=item,
            status='pending',
            start_date__lte=request_obj.end_date,
            end_date__gte=request_obj.start_date
        ).exclude(id=request_obj.id)

        # Decline conflicting requests and notify their borrowers
        for conflict in overlapping_pending:
            conflict.status = 'declined'
            conflict.decline_reason = 'Item booked for overlapping dates'
            conflict.save(update_fields=['status', 'decline_reason'])

            Notification.objects.create(
                recipient=conflict.borrower,
                message=f"Your request for {item.title} was declined: Item booked for overlapping dates.",
                link=f"/borrowing/{conflict.id}/"
            )

        # Approve the target request
        request_obj.status = 'approved'
        request_obj.save(update_fields=['status'])

        # Notify the approved borrower
        Notification.objects.create(
            recipient=request_obj.borrower,
            message=f"Good news! Your request for '{item.title}' has been approved.",
            link=f"/borrowing/{request_obj.id}/"
        )

        return request_obj


def activate_if_due(user):
    """
    Synchronizes overdue statuses and activates any approved requests associated with
    the user whose start_date has arrived.
    """
    sync_overdue_statuses()

    today = timezone.now().date()
    due_requests = BorrowRequest.objects.filter(
        Q(borrower=user) | Q(item__owner=user),
        status='approved',
        start_date__lte=today
    )

    updated_count = due_requests.update(status='active')
    return updated_count


def mark_returned(request_obj, condition, note=''):
    """
    Finalizes the return of an item, logs return condition and timestamp,
    updates item condition, and notifies the borrower.
    """
    with transaction.atomic():
        now = timezone.now()
        request_obj.status = 'returned'
        request_obj.returned_at = now
        request_obj.return_condition = condition
        request_obj.return_note = note
        request_obj.save(update_fields=['status', 'returned_at', 'return_condition', 'return_note'])

        # Update item condition
        item = request_obj.item
        item.condition = condition
        item.save(update_fields=['condition'])

        # Notify borrower
        Notification.objects.create(
            recipient=request_obj.borrower,
            message=f"Return confirmed for '{item.title}'. Recorded condition: {request_obj.get_return_condition_display()}.",
            link=f"/borrowing/{request_obj.id}/"
        )

        return request_obj
