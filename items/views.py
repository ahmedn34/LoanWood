from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q, F
from django.contrib.postgres.search import SearchQuery, SearchRank
from .models import Item, Category
from .forms import ItemForm
from borrowing.forms import BorrowRequestForm
from accounts.services import get_reputation_stats


def browse_items(request):
    """
    Catalog view filtering active tools with PostgreSQL full-text search,
    category taxonomy filters, and pagination.
    """
    queryset = Item.objects.filter(
        is_deleted=False,
        is_available=True
    ).select_related('owner', 'category')

    # Category filtering
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        queryset = queryset.filter(category=selected_category)

    # Search filtering
    q = request.GET.get('q', '').strip()
    if q:
        if connection.vendor == 'postgresql':
            query = SearchQuery(q)
            queryset = queryset.filter(search_vector=query).annotate(
                rank=SearchRank(F('search_vector'), query)
            ).order_by('-rank', '-created_at')
        else:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            ).order_by('-created_at')
    else:
        queryset = queryset.order_by('-created_at')

    # Pagination
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    categories = Category.objects.all()

    return render(request, 'items/browse_items.html', {
        'items': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'q': q,
    })


def item_detail(request, pk):
    """
    Tool detail view displaying tool specifications, owner bio/stats,
    and embedded borrow request form.
    """
    item = get_object_or_404(
        Item.objects.select_related('owner', 'owner__profile', 'category'),
        pk=pk,
        is_deleted=False
    )
    owner_stats = get_reputation_stats(item.owner)
    borrow_form = BorrowRequestForm(item=item)

    return render(request, 'items/item_detail.html', {
        'item': item,
        'owner_stats': owner_stats,
        'borrow_form': borrow_form,
        'is_owner': request.user.is_authenticated and request.user == item.owner,
        'currently_borrowed': item.currently_borrowed(),
    })


@login_required
def item_create(request):
    """Creates a new tool catalog entry owned by the requesting user."""
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            messages.success(request, f"'{item.title}' has been added to the neighborhood catalog!")
            return redirect('items:detail', pk=item.pk)
    else:
        form = ItemForm()

    return render(request, 'items/item_form.html', {
        'form': form,
        'action_title': 'Add a Tool to Community',
    })


@login_required
def item_update(request, pk):
    """Updates tool details, restricted to the tool owner."""
    item = get_object_or_404(Item, pk=pk, is_deleted=False)
    if item.owner != request.user:
        messages.error(request, "You are not authorized to edit this tool.")
        return redirect('items:detail', pk=item.pk)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{item.title}' has been updated.")
            return redirect('items:detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)

    return render(request, 'items/item_form.html', {
        'form': form,
        'item': item,
        'action_title': f"Edit {item.title}",
    })


@login_required
def item_delete(request, pk):
    """Soft-deletes a tool setting is_deleted=True and is_available=False."""
    item = get_object_or_404(Item, pk=pk, is_deleted=False)
    if item.owner != request.user:
        messages.error(request, "You are not authorized to remove this tool.")
        return redirect('items:detail', pk=item.pk)

    if request.method == 'POST':
        item.is_deleted = True
        item.is_available = False
        item.save(update_fields=['is_deleted', 'is_available'])
        messages.success(request, f"'{item.title}' has been removed from the catalog. Historical lending records have been safely preserved.")
        return redirect('borrowing:owner_dashboard')

    return render(request, 'items/item_confirm_delete.html', {'item': item})
