"""
Serializers for grocery items and purchases.
"""

from django.db import models
from rest_framework import serializers
from .models import GroceryItem, Purchase


class GroceryItemSerializer(serializers.ModelSerializer):
    """
    Full CRUD serializer for GroceryItem.
    The `user` field is set automatically from the request — never from client input.
    """
    # Read-only computed field: how many times this item has been purchased
    purchase_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = GroceryItem
        fields = [
            'id', 'name', 'unit_type', 'default_price_per_unit',
            'category', 'purchase_count', 'total_spent',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_purchase_count(self, obj):
        """Total number of purchases for this item."""
        return obj.purchases.count()

    def get_total_spent(self, obj):
        """Total money spent on this item across all purchases."""
        total = obj.purchases.aggregate(
            total=models.Sum('total_price')
        )['total']
        return str(total or '0.00')

    def validate_name(self, value):
        """Ensure item name is unique per user (case-insensitive)."""
        user = self.context['request'].user
        qs = GroceryItem.objects.filter(user=user, name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f"You already have an item named '{value}'."
            )
        return value


class PurchaseSerializer(serializers.ModelSerializer):
    """
    Full CRUD serializer for Purchase.
    Shows nested item details on read, accepts item ID on write.
    """
    # Read-only nested info
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_unit_type = serializers.CharField(source='item.unit_type', read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = Purchase
        fields = [
            'id', 'item', 'item_name', 'item_unit_type',
            'quantity', 'price_per_unit', 'total_price',
            'purchased_at', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']

    def validate_item(self, value):
        """Ensure the item belongs to the authenticated user."""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("This item does not belong to you.")
        return value


class PurchaseCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating purchases.
    If price_per_unit is not provided, uses the item's default price.
    """

    class Meta:
        model = Purchase
        fields = [
            'id', 'item', 'quantity', 'price_per_unit',
            'purchased_at', 'notes',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'price_per_unit': {'required': False},
            'purchased_at': {'required': False},
        }

    def validate_item(self, value):
        """Ensure the item belongs to the authenticated user."""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("This item does not belong to you.")
        return value

    def create(self, validated_data):
        """Auto-fill price_per_unit from item default if not provided."""
        if 'price_per_unit' not in validated_data or validated_data['price_per_unit'] is None:
            validated_data['price_per_unit'] = validated_data['item'].default_price_per_unit
        return super().create(validated_data)
