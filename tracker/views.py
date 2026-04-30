"""
Views for grocery items, purchases, and spending reports.
"""

from datetime import datetime
from decimal import Decimal

from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import GroceryItem, Purchase
from .serializers import GroceryItemSerializer, PurchaseSerializer, PurchaseCreateSerializer
from .filters import PurchaseFilter


# ─────────────────────────────────────────────────────────────────────
# GROCERY ITEMS — Full CRUD ViewSet
# ─────────────────────────────────────────────────────────────────────

class GroceryItemViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for grocery items.

    list:    GET    /api/items/         — List all your grocery items
    create:  POST   /api/items/         — Add a new item
    read:    GET    /api/items/{id}/    — Get item details
    update:  PUT    /api/items/{id}/    — Update an item
    partial: PATCH  /api/items/{id}/    — Partially update an item
    delete:  DELETE /api/items/{id}/    — Delete an item
    """
    serializer_class = GroceryItemSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'category']
    ordering_fields = ['name', 'default_price_per_unit', 'created_at']

    def get_queryset(self):
        """Only return items belonging to the authenticated user."""
        return GroceryItem.objects.filter(user=self.request.user).prefetch_related('purchases')

    def perform_create(self, serializer):
        """Automatically set the user to the authenticated user."""
        serializer.save(user=self.request.user)


# ─────────────────────────────────────────────────────────────────────
# PURCHASES — Full CRUD ViewSet with Filtering
# ─────────────────────────────────────────────────────────────────────

class PurchaseViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for purchases.

    list:    GET    /api/purchases/         — List purchases (with filters)
    create:  POST   /api/purchases/         — Record a new purchase
    read:    GET    /api/purchases/{id}/    — Get purchase details
    update:  PUT    /api/purchases/{id}/    — Update a purchase
    partial: PATCH  /api/purchases/{id}/    — Partially update a purchase
    delete:  DELETE /api/purchases/{id}/    — Delete a purchase

    Filters:
    - ?item=<id>            — Filter by item
    - ?item_name=<text>     — Search by item name
    - ?date_from=YYYY-MM-DD — From date
    - ?date_to=YYYY-MM-DD   — To date
    - ?month=1-12           — Filter by month
    - ?year=2026            — Filter by year
    """
    permission_classes = [IsAuthenticated]
    filterset_class = PurchaseFilter
    search_fields = ['item__name', 'notes']
    ordering_fields = ['purchased_at', 'total_price', 'quantity']

    def get_queryset(self):
        """Only return purchases belonging to the authenticated user."""
        return Purchase.objects.filter(
            user=self.request.user
        ).select_related('item')

    def get_serializer_class(self):
        """Use a simpler serializer for create/update."""
        if self.action in ('create',):
            return PurchaseCreateSerializer
        return PurchaseSerializer

    def perform_create(self, serializer):
        """Automatically set the user to the authenticated user."""
        serializer.save(user=self.request.user)


# ─────────────────────────────────────────────────────────────────────
# REPORTS — Monthly Summary
# ─────────────────────────────────────────────────────────────────────

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='month', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
            description='Month number (1-12). Defaults to current month.',
        ),
        OpenApiParameter(
            name='year', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
            description='Year (e.g., 2026). Defaults to current year.',
        ),
    ],
    description="Get a spending summary for a specific month. Shows total spent, item-wise breakdown, and daily totals.",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_summary(request):
    """
    Monthly spending summary.
    Query params: ?month=4&year=2026  (defaults to current month/year)
    """
    now = timezone.now()
    month = int(request.query_params.get('month', now.month))
    year = int(request.query_params.get('year', now.year))

    purchases = Purchase.objects.filter(
        user=request.user,
        purchased_at__month=month,
        purchased_at__year=year,
    ).select_related('item')

    # Overall totals
    totals = purchases.aggregate(
        total_spent=Sum('total_price'),
        total_purchases=Count('id'),
    )

    # Item-wise breakdown
    item_breakdown = (
        purchases
        .values('item__name', 'item__unit_type')
        .annotate(
            times_bought=Count('id'),
            total_quantity=Sum('quantity'),
            total_spent=Sum('total_price'),
        )
        .order_by('-total_spent')
    )

    # Daily totals
    daily_breakdown = (
        purchases
        .annotate(date=TruncDate('purchased_at'))
        .values('date')
        .annotate(
            day_total=Sum('total_price'),
            purchase_count=Count('id'),
        )
        .order_by('date')
    )

    return Response({
        'month': month,
        'year': year,
        'total_spent': str(totals['total_spent'] or '0.00'),
        'total_purchases': totals['total_purchases'],
        'item_breakdown': [
            {
                'item_name': item['item__name'],
                'unit_type': item['item__unit_type'],
                'times_bought': item['times_bought'],
                'total_quantity': str(item['total_quantity']),
                'total_spent': str(item['total_spent']),
            }
            for item in item_breakdown
        ],
        'daily_breakdown': [
            {
                'date': day['date'].isoformat(),
                'total_spent': str(day['day_total']),
                'purchase_count': day['purchase_count'],
            }
            for day in daily_breakdown
        ],
    })


# ─────────────────────────────────────────────────────────────────────
# REPORTS — Item Frequency (how many times each item was bought)
# ─────────────────────────────────────────────────────────────────────

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='month', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
            description='Optional month filter (1-12).',
        ),
        OpenApiParameter(
            name='year', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
            description='Optional year filter.',
        ),
    ],
    description="Shows how many times each item was bought, total quantity, and total spent. Optionally filtered by month/year.",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def item_frequency(request):
    """
    How many times each item was purchased + total spent per item.
    Optional filters: ?month=4&year=2026
    """
    purchases = Purchase.objects.filter(user=request.user)

    month = request.query_params.get('month')
    year = request.query_params.get('year')
    if month:
        purchases = purchases.filter(purchased_at__month=int(month))
    if year:
        purchases = purchases.filter(purchased_at__year=int(year))

    frequency = (
        purchases
        .values('item__id', 'item__name', 'item__unit_type', 'item__category')
        .annotate(
            times_bought=Count('id'),
            total_quantity=Sum('quantity'),
            total_spent=Sum('total_price'),
            avg_price_per_unit=Sum('total_price') / Sum('quantity'),
        )
        .order_by('-times_bought')
    )

    return Response({
        'filters': {'month': month, 'year': year},
        'items': [
            {
                'item_id': f['item__id'],
                'item_name': f['item__name'],
                'unit_type': f['item__unit_type'],
                'category': f['item__category'],
                'times_bought': f['times_bought'],
                'total_quantity': str(f['total_quantity']),
                'total_spent': str(f['total_spent']),
                'avg_price_per_unit': str(round(f['avg_price_per_unit'], 2)),
            }
            for f in frequency
        ],
    })


# ─────────────────────────────────────────────────────────────────────
# REPORTS — Daily Breakdown (day-by-day with individual purchase times)
# ─────────────────────────────────────────────────────────────────────

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='month', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
            description='Month (1-12). Defaults to current month.',
        ),
        OpenApiParameter(
            name='year', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
            description='Year. Defaults to current year.',
        ),
        OpenApiParameter(
            name='date', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY,
            description='Specific date (YYYY-MM-DD) to see all purchases for that day.',
        ),
    ],
    description="Day-by-day spending breakdown showing each purchase with exact timestamps.",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_breakdown(request):
    """
    Day-by-day spending with individual purchase timestamps.
    - ?month=4&year=2026   → all days in April 2026
    - ?date=2026-04-30     → all purchases on that specific date
    """
    purchases = Purchase.objects.filter(user=request.user).select_related('item')

    specific_date = request.query_params.get('date')

    if specific_date:
        # Show all purchases for a specific date
        target_date = datetime.strptime(specific_date, '%Y-%m-%d').date()
        purchases = purchases.filter(purchased_at__date=target_date)

        purchase_list = [
            {
                'id': p.id,
                'item_name': p.item.name,
                'unit_type': p.item.unit_type,
                'quantity': str(p.quantity),
                'price_per_unit': str(p.price_per_unit),
                'total_price': str(p.total_price),
                'time': p.purchased_at.strftime('%H:%M:%S'),
                'purchased_at': p.purchased_at.isoformat(),
                'notes': p.notes,
            }
            for p in purchases
        ]

        day_total = purchases.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

        return Response({
            'date': specific_date,
            'total_spent': str(day_total),
            'purchase_count': len(purchase_list),
            'purchases': purchase_list,
        })

    else:
        # Monthly daily breakdown
        now = timezone.now()
        month = int(request.query_params.get('month', now.month))
        year = int(request.query_params.get('year', now.year))

        purchases = purchases.filter(
            purchased_at__month=month,
            purchased_at__year=year,
        )

        # Group by date
        daily_data = {}
        for p in purchases:
            date_key = p.purchased_at.date().isoformat()
            if date_key not in daily_data:
                daily_data[date_key] = {
                    'date': date_key,
                    'total_spent': Decimal('0.00'),
                    'purchases': [],
                }
            daily_data[date_key]['total_spent'] += p.total_price
            daily_data[date_key]['purchases'].append({
                'id': p.id,
                'item_name': p.item.name,
                'quantity': str(p.quantity),
                'price_per_unit': str(p.price_per_unit),
                'total_price': str(p.total_price),
                'time': p.purchased_at.strftime('%H:%M:%S'),
                'notes': p.notes,
            })

        # Convert to list and stringify decimals
        result = []
        for date_key in sorted(daily_data.keys()):
            day = daily_data[date_key]
            day['total_spent'] = str(day['total_spent'])
            day['purchase_count'] = len(day['purchases'])
            result.append(day)

        month_total = purchases.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

        return Response({
            'month': month,
            'year': year,
            'month_total': str(month_total),
            'days': result,
        })
