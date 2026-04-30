"""
Filters for purchase queries — filter by date range, item, etc.
"""

import django_filters
from .models import Purchase


class PurchaseFilter(django_filters.FilterSet):
    """
    Filter purchases by:
    - date_from / date_to  → purchased_at range
    - item                 → specific item ID
    - item_name            → search by item name (case-insensitive contains)
    - month                → specific month (1-12)
    - year                 → specific year
    """
    date_from = django_filters.DateTimeFilter(
        field_name='purchased_at',
        lookup_expr='gte',
        label='From date (YYYY-MM-DD)',
    )
    date_to = django_filters.DateTimeFilter(
        field_name='purchased_at',
        lookup_expr='lte',
        label='To date (YYYY-MM-DD)',
    )
    item_name = django_filters.CharFilter(
        field_name='item__name',
        lookup_expr='icontains',
        label='Item name contains',
    )
    month = django_filters.NumberFilter(
        field_name='purchased_at',
        lookup_expr='month',
        label='Month (1-12)',
    )
    year = django_filters.NumberFilter(
        field_name='purchased_at',
        lookup_expr='year',
        label='Year (e.g., 2026)',
    )

    class Meta:
        model = Purchase
        fields = ['item', 'date_from', 'date_to', 'item_name', 'month', 'year']
