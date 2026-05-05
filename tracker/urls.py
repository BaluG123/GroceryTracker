"""
URL routes for the grocery tracker.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'items', views.GroceryItemViewSet, basename='groceryitem')
router.register(r'expense-items', views.GroceryItemViewSet, basename='expenseitem')
router.register(r'purchases', views.PurchaseViewSet, basename='purchase')
router.register(r'expenses', views.PurchaseViewSet, basename='expense')

urlpatterns = [
    path('', include(router.urls)),
    path('reports/monthly-summary/', views.monthly_summary, name='monthly-summary'),
    path('reports/item-frequency/', views.item_frequency, name='item-frequency'),
    path('reports/daily-breakdown/', views.daily_breakdown, name='daily-breakdown'),
]
