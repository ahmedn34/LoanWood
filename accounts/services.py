from django.db.models import Count, F, Q
from items.models import Item
from borrowing.models import BorrowRequest


def get_reputation_stats(user):
    """
    Computes dynamic lending reputation and trust metrics for a community member.
    """
    returned_requests = BorrowRequest.objects.filter(
        borrower=user,
        status='returned'
    )
    total_borrows = returned_requests.count()

    if total_borrows > 0:
        on_time_count = returned_requests.filter(
            returned_at__date__lte=F('end_date')
        ).count()
        on_time_rate = round((on_time_count / total_borrows) * 100)
    else:
        on_time_rate = None

    damaged_returns = returned_requests.filter(
        return_condition__in=['fair', 'worn']
    ).count()

    items_owned = user.items.filter(is_deleted=False).count()

    return {
        'total_borrows': total_borrows,
        'on_time_rate': on_time_rate,
        'damaged_returns': damaged_returns,
        'items_owned': items_owned,
    }


def get_most_borrowed_items(limit=8):
    """
    Returns non-deleted tools ordered by frequency of approved/active/historical borrow transactions.
    """
    return Item.objects.filter(is_deleted=False).annotate(
        borrow_count=Count(
            'requests',
            filter=Q(requests__status__in=['approved', 'active', 'returned', 'overdue'])
        )
    ).order_by('-borrow_count', '-created_at')[:limit]
