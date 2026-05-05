"""
Models for tracking day-to-day spending.

GroceryItem remains the underlying table name for backward compatibility,
but the model now represents any user-defined expense item.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class GroceryItem(models.Model):
    """
    A reusable expense item template.
    Examples: Milk, Bus Ticket, Coffee, Mobile Recharge, Rent.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grocery_items',
    )
    name = models.CharField(max_length=100)
    unit_type = models.CharField(
        max_length=30,
        default='unit',
        help_text="Flexible unit label, e.g., kg, litre, trip, month, meal, ticket.",
    )
    default_price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Default/usual price per unit. Can be overridden per purchase.",
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Optional spending category, e.g., Groceries, Transport, Bills, Health.",
    )
    description = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name} ({self.unit_type}) - {self.default_price_per_unit}"


class Purchase(models.Model):
    """
    A single expense or purchase event.
    Snapshot fields preserve history even if the reusable item later changes.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchases',
    )
    item = models.ForeignKey(
        GroceryItem,
        on_delete=models.SET_NULL,
        related_name='purchases',
        null=True,
        blank=True,
    )
    item_name_snapshot = models.CharField(max_length=100, blank=True, default='')
    unit_type_snapshot = models.CharField(max_length=30, blank=True, default='')
    category_snapshot = models.CharField(max_length=50, blank=True, default='')
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Number of units bought, e.g., 2 litres, 1 trip, 1 month.",
    )
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Actual price paid per unit for this purchase.",
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False,
        help_text="Auto-calculated: quantity × price_per_unit.",
    )
    purchased_at = models.DateTimeField(
        default=timezone.now,
        help_text="Exact date and time of purchase.",
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text="Optional notes about the expense.",
    )
    merchant_name = models.CharField(max_length=120, blank=True, default='')
    payment_method = models.CharField(max_length=30, blank=True, default='')
    currency_code = models.CharField(max_length=3, default='INR')
    location = models.CharField(max_length=120, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchased_at']

    def save(self, *args, **kwargs):
        """Auto-calculate total_price and keep an item snapshot."""
        if self.item:
            self.item_name_snapshot = self.item.name
            self.unit_type_snapshot = self.item.unit_type
            self.category_snapshot = self.item.category
        self.total_price = self.quantity * self.price_per_unit
        super().save(*args, **kwargs)

    def __str__(self):
        item_name = self.item_name_snapshot or (self.item.name if self.item else 'Expense')
        unit_type = self.unit_type_snapshot or (self.item.unit_type if self.item else 'unit')
        return (
            f"{item_name} x {self.quantity} {unit_type} "
            f"= {self.currency_code} {self.total_price} on {self.purchased_at:%Y-%m-%d %H:%M}"
        )
