from django.shortcuts import render
from items.models import Category
from accounts.services import get_most_borrowed_items


def home_view(request):
    """Landing page featuring community categories and trending borrowed tools."""
    categories = Category.objects.all()
    most_borrowed = get_most_borrowed_items(limit=6)

    return render(request, 'core/home.html', {
        'categories': categories,
        'most_borrowed': most_borrowed,
    })
