from django.urls import path
from . import views

app_name = 'items'

urlpatterns = [
    path('', views.browse_items, name='list'),
    path('browse/', views.browse_items, name='browse'),
    path('add/', views.item_create, name='create'),
    path('<int:pk>/', views.item_detail, name='detail'),
    path('<int:pk>/edit/', views.item_update, name='update'),
    path('<int:pk>/delete/', views.item_delete, name='delete'),
]
