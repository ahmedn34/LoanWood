def global_context(request):
    """
    Context processor providing global template context across Loanwood.
    Safely calculates unread notifications count for authenticated users.
    """
    unread_notifications_count = 0
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            if hasattr(request.user, 'notifications'):
                unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        except Exception:
            unread_notifications_count = 0

    return {
        'unread_notifications_count': unread_notifications_count,
    }
