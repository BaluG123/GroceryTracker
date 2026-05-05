"""
Admin registration for expense tracker models.
"""

from django.contrib import admin
from .models import GroceryItem, Purchase


@admin.register(GroceryItem)
class GroceryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'unit_type', 'default_price_per_unit', 'category', 'is_active', 'created_at']
    list_filter = ['unit_type', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'category', 'description', 'user__username']
    ordering = ['name']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['item_name_snapshot', 'user', 'quantity', 'price_per_unit', 'total_price', 'currency_code', 'purchased_at']
    list_filter = ['purchased_at', 'category_snapshot', 'payment_method', 'currency_code']
    search_fields = ['item_name_snapshot', 'merchant_name', 'location', 'user__username', 'notes']
    ordering = ['-purchased_at']
    date_hierarchy = 'purchased_at'
