"""
Admin registration for grocery tracker models.
"""

from django.contrib import admin
from .models import GroceryItem, Purchase


@admin.register(GroceryItem)
class GroceryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'unit_type', 'default_price_per_unit', 'category', 'created_at']
    list_filter = ['unit_type', 'category', 'created_at']
    search_fields = ['name', 'category', 'user__username']
    ordering = ['name']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['item', 'user', 'quantity', 'price_per_unit', 'total_price', 'purchased_at']
    list_filter = ['purchased_at', 'item__name', 'item__category']
    search_fields = ['item__name', 'user__username', 'notes']
    ordering = ['-purchased_at']
    date_hierarchy = 'purchased_at'
