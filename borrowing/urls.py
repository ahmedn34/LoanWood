from django.urls import path
from . import views

app_name = 'borrowing'

urlpatterns = [
    path('dashboard/', views.borrower_dashboard, name='borrower_dashboard'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('request/<int:item_pk>/', views.create_borrow_request, name='create_request'),
    path('requests/<int:pk>/approve/', views.approve_borrow_request, name='approve_request'),
    path('requests/<int:pk>/decline/', views.decline_borrow_request, name='decline_request'),
    path('requests/<int:pk>/return/', views.mark_item_returned, name='mark_returned'),
    path('requests/<int:pk>/cancel/', views.cancel_borrow_request, name='cancel_request'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
