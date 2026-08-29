from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'neighborhood', 'created_at')
    list_filter = ('neighborhood', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'neighborhood', 'bio')
    readonly_fields = ('created_at',)
