"""
Models for the grocery expense tracker.

GroceryItem — master catalog of items a user tracks.
Purchase    — every individual purchase event with date, time, quantity, price.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class GroceryItem(models.Model):
    """
    A grocery item that the user buys regularly.
    e.g., Milk, Rice, Tomato, Bread, Eggs, etc.
    """

    UNIT_CHOICES = [
        ('litre', 'Litre'),
        ('ml', 'Millilitre'),
        ('kg', 'Kilogram'),
        ('gram', 'Gram'),
        ('packet', 'Packet'),
        ('piece', 'Piece'),
        ('dozen', 'Dozen'),
        ('bundle', 'Bundle'),
        ('box', 'Box'),
        ('bottle', 'Bottle'),
        ('can', 'Can'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grocery_items',
    )
    name = models.CharField(max_length=100)
    unit_type = models.CharField(max_length=30, choices=UNIT_CHOICES, default='piece')
    default_price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Default/usual price per unit. Can be overridden per purchase.",
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Optional category, e.g., Dairy, Vegetables, Grains, Snacks.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        # Prevent duplicate item names per user
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name} ({self.unit_type}) — ₹{self.default_price_per_unit}"


class Purchase(models.Model):
    """
    A single purchase event.
    Tracks exactly what was bought, how many units, at what price,
    and the exact date & time of purchase.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchases',
    )
    item = models.ForeignKey(
        GroceryItem,
        on_delete=models.CASCADE,
        related_name='purchases',
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Number of units bought (e.g., 2 litres, 0.5 kg).",
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
        help_text="Optional notes, e.g., 'bought from local market'.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchased_at']

    def save(self, *args, **kwargs):
        """Auto-calculate total_price before saving."""
        self.total_price = self.quantity * self.price_per_unit
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.item.name} × {self.quantity} {self.item.unit_type} "
            f"= ₹{self.total_price} on {self.purchased_at:%Y-%m-%d %H:%M}"
        )
