from django.contrib import admin
from .models import Category, Item


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'owner',
        'category',
        'condition',
        'is_available',
        'is_deleted',
        'currently_borrowed_status',
        'created_at',
    )
    list_filter = ('condition', 'is_available', 'is_deleted', 'category', 'created_at')
    search_fields = ('title', 'description', 'owner__username', 'owner__email', 'category__name')
    readonly_fields = ('search_vector', 'created_at')
    actions = ['soft_delete_items', 'restore_items']

    @admin.display(boolean=True, description='Currently Borrowed')
    def currently_borrowed_status(self, obj):
        return obj.currently_borrowed()

    @admin.action(description='Soft-delete selected tools')
    def soft_delete_items(self, request, queryset):
        queryset.update(is_deleted=True, is_available=False)

    @admin.action(description='Restore soft-deleted tools')
    def restore_items(self, request, queryset):
        queryset.update(is_deleted=False, is_available=True)
