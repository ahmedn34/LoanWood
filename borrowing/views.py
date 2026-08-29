from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from items.models import Item
from .models import BorrowRequest, Notification
from .forms import BorrowRequestForm, ReturnItemForm, DeclineRequestForm
from . import services


@login_required
def create_borrow_request(request, item_pk):
    """Submits a borrow request, barring tool owners from requesting their own gear."""
    item = get_object_or_404(Item, pk=item_pk, is_deleted=False)

    if item.owner == request.user:
        messages.error(request, "You cannot borrow your own tool.")
        return redirect('items:detail', pk=item.pk)

    if request.method == 'POST':
        form = BorrowRequestForm(request.POST, item=item)
        if form.is_valid():
            borrow_req = form.save(commit=False)
            borrow_req.borrower = request.user
            borrow_req.item = item
            borrow_req.status = 'pending'
            borrow_req.save()

            # Notify tool owner
            Notification.objects.create(
                recipient=item.owner,
                message=f"New borrow request from {request.user.username} for '{item.title}'.",
                link=f"/borrowing/owner/"
            )

            messages.success(request, f"Borrow request for '{item.title}' submitted to {item.owner.username}!")
            return redirect('borrowing:borrower_dashboard')
    else:
        form = BorrowRequestForm(item=item)

    return render(request, 'borrowing/create_request.html', {
        'form': form,
        'item': item,
    })


@login_required
def approve_borrow_request(request, pk):
    """Owner action approving a pending request and resolving conflicting overlaps."""
    borrow_req = get_object_or_404(BorrowRequest.objects.select_related('item', 'item__owner'), pk=pk)
    if borrow_req.item.owner != request.user:
        messages.error(request, "You are not authorized to approve this request.")
        return redirect('borrowing:owner_dashboard')

    if borrow_req.status != 'pending':
        messages.warning(request, f"This request is currently '{borrow_req.status}' and cannot be approved.")
        return redirect('borrowing:owner_dashboard')

    if request.method == 'POST':
        services.approve_request(borrow_req)
        messages.success(request, f"Request approved! '{borrow_req.item.title}' is reserved for {borrow_req.borrower.username}.")
        return redirect('borrowing:owner_dashboard')

    return render(request, 'borrowing/confirm_approve.html', {'borrow_req': borrow_req})


@login_required
def decline_borrow_request(request, pk):
    """Owner action declining a borrow request with an explicit reason."""
    borrow_req = get_object_or_404(BorrowRequest.objects.select_related('item', 'item__owner'), pk=pk)
    if borrow_req.item.owner != request.user:
        messages.error(request, "You are not authorized to decline this request.")
        return redirect('borrowing:owner_dashboard')

    if request.method == 'POST':
        form = DeclineRequestForm(request.POST, instance=borrow_req)
        if form.is_valid():
            req_obj = form.save(commit=False)
            req_obj.status = 'declined'
            req_obj.save(update_fields=['status', 'decline_reason'])

            Notification.objects.create(
                recipient=borrow_req.borrower,
                message=f"Your request for '{borrow_req.item.title}' was declined: {req_obj.decline_reason}",
                link=f"/borrowing/dashboard/"
            )

            messages.info(request, f"Request from {borrow_req.borrower.username} has been declined.")
            return redirect('borrowing:owner_dashboard')
    else:
        form = DeclineRequestForm(instance=borrow_req)

    return render(request, 'borrowing/decline_request.html', {
        'form': form,
        'borrow_req': borrow_req,
    })


@login_required
def mark_item_returned(request, pk):
    """Owner audits returned item, evaluates condition, and finalizes transaction."""
    borrow_req = get_object_or_404(BorrowRequest.objects.select_related('item', 'item__owner'), pk=pk)
    if borrow_req.item.owner != request.user:
        messages.error(request, "You are not authorized to record returns for this tool.")
        return redirect('borrowing:owner_dashboard')

    if borrow_req.status not in ['active', 'overdue', 'approved']:
        messages.warning(request, f"Cannot record return for request in '{borrow_req.status}' status.")
        return redirect('borrowing:owner_dashboard')

    if request.method == 'POST':
        form = ReturnItemForm(request.POST, instance=borrow_req)
        if form.is_valid():
            condition = form.cleaned_data['return_condition']
            note = form.cleaned_data['return_note']
            services.mark_returned(borrow_req, condition=condition, note=note)
            messages.success(request, f"Return recorded for '{borrow_req.item.title}'. Tool condition updated to {borrow_req.get_return_condition_display()}.")
            return redirect('borrowing:owner_dashboard')
    else:
        form = ReturnItemForm(instance=borrow_req, initial={'return_condition': borrow_req.item.condition})

    return render(request, 'borrowing/return_form.html', {
        'form': form,
        'borrow_req': borrow_req,
    })


@login_required
def cancel_borrow_request(request, pk):
    """Borrower cancels their pending request."""
    borrow_req = get_object_or_404(BorrowRequest, pk=pk, borrower=request.user)
    if borrow_req.status != 'pending':
        messages.error(request, "Only pending requests can be cancelled.")
        return redirect('borrowing:borrower_dashboard')

    if request.method == 'POST':
        borrow_req.status = 'cancelled'
        borrow_req.save(update_fields=['status'])
        messages.info(request, "Your borrow request has been cancelled.")
        return redirect('borrowing:borrower_dashboard')

    return render(request, 'borrowing/confirm_cancel.html', {'borrow_req': borrow_req})


@login_required
def borrower_dashboard(request):
    """Borrower view with automatic status sync and grouped request categories."""
    services.activate_if_due(request.user)

    user_requests = BorrowRequest.objects.filter(borrower=request.user).select_related('item', 'item__owner')

    active_overdue = user_requests.filter(status__in=['active', 'overdue'])
    pending = user_requests.filter(status='pending')
    history = user_requests.filter(status__in=['returned', 'declined', 'cancelled'])

    return render(request, 'borrowing/borrower_dashboard.html', {
        'active_overdue': active_overdue,
        'pending': pending,
        'history': history,
    })


@login_required
def owner_dashboard(request):
    """Owner view showing owned tools, incoming requests, and lent gear."""
    services.activate_if_due(request.user)

    my_items = request.user.items.filter(is_deleted=False)
    pending_incoming = BorrowRequest.objects.filter(
        item__owner=request.user,
        status='pending'
    ).select_related('item', 'borrower')

    currently_lent = BorrowRequest.objects.filter(
        item__owner=request.user,
        status__in=['approved', 'active', 'overdue']
    ).select_related('item', 'borrower')

    return render(request, 'borrowing/owner_dashboard.html', {
        'my_items': my_items,
        'pending_incoming': pending_incoming,
        'currently_lent': currently_lent,
    })


@login_required
def notifications_list(request):
    """Lists community notifications for current user."""
    notifications = request.user.notifications.all()
    return render(request, 'borrowing/notifications.html', {
        'notifications': notifications
    })


@login_required
def mark_notification_read_view(request, pk):
    """Marks a single notification as read and navigates to target link."""
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])

    if notif.link:
        return redirect(notif.link)
    return redirect('borrowing:notifications')


@login_required
def mark_all_notifications_read(request):
    """Marks all unread notifications for the user as read."""
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
    return redirect('borrowing:notifications')
