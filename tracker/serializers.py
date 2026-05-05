"""
Serializers for reusable expense items and expense records.
"""

from django.db import models
from rest_framework import serializers
from .models import GroceryItem, Purchase


class GroceryItemSerializer(serializers.ModelSerializer):
    """
    Full CRUD serializer for reusable expense items.
    """
    purchase_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    unit_label = serializers.CharField(source='unit_type', read_only=True)

    class Meta:
        model = GroceryItem
        fields = [
            'id', 'name', 'unit_type', 'unit_label', 'default_price_per_unit',
            'description', 'is_active',
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

    def validate_unit_type(self, value):
        cleaned = value.strip().lower()
        if not cleaned:
            raise serializers.ValidationError("Unit type cannot be blank.")
        return cleaned


class PurchaseSerializer(serializers.ModelSerializer):
    """
    Full serializer for expense records.
    """
    item_name = serializers.SerializerMethodField()
    item_unit_type = serializers.SerializerMethodField()
    item_category = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = Purchase
        fields = [
            'id', 'item', 'item_name', 'item_unit_type', 'item_category',
            'quantity', 'price_per_unit', 'total_price',
            'purchased_at', 'notes', 'merchant_name', 'payment_method',
            'currency_code', 'location',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']

    def validate_item(self, value):
        """Ensure the item belongs to the authenticated user."""
        user = self.context['request'].user
        if value and value.user != user:
            raise serializers.ValidationError("This item does not belong to you.")
        return value

    def get_item_name(self, obj):
        return obj.item_name_snapshot or (obj.item.name if obj.item else '')

    def get_item_unit_type(self, obj):
        return obj.unit_type_snapshot or (obj.item.unit_type if obj.item else '')

    def get_item_category(self, obj):
        return obj.category_snapshot or (obj.item.category if obj.item else '')


class PurchaseCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer for expense records.
    """
    item = serializers.PrimaryKeyRelatedField(
        queryset=GroceryItem.objects.all(),
        required=False,
        allow_null=True,
    )
    item_name = serializers.CharField(required=False, allow_blank=False)
    item_unit_type = serializers.CharField(required=False, allow_blank=True)
    item_category = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'item', 'item_name', 'item_unit_type', 'item_category',
            'quantity', 'price_per_unit', 'purchased_at', 'notes',
            'merchant_name', 'payment_method', 'currency_code', 'location',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'price_per_unit': {'required': False},
            'purchased_at': {'required': False},
            'currency_code': {'required': False},
        }

    def validate_item(self, value):
        """Ensure the item belongs to the authenticated user."""
        user = self.context['request'].user
        if value and value.user != user:
            raise serializers.ValidationError("This item does not belong to you.")
        return value

    def validate(self, attrs):
        item = attrs.get('item')
        item_name = attrs.get('item_name', '').strip()
        if not item and not item_name:
            raise serializers.ValidationError({'item_name': 'Provide an existing item or an item name.'})
        if attrs.get('currency_code'):
            attrs['currency_code'] = attrs['currency_code'].upper()
        else:
            attrs['currency_code'] = 'INR'
        if 'item_unit_type' in attrs:
            attrs['item_unit_type'] = attrs['item_unit_type'].strip().lower()
        return attrs

    def create(self, validated_data):
        """Auto-fill snapshot data and price from the reusable item when available."""
        item_name = validated_data.pop('item_name', '').strip()
        item_unit_type = validated_data.pop('item_unit_type', '').strip().lower()
        item_category = validated_data.pop('item_category', '').strip()
        item = validated_data.get('item')

        if 'price_per_unit' not in validated_data or validated_data['price_per_unit'] is None:
            if item:
                validated_data['price_per_unit'] = item.default_price_per_unit
            else:
                raise serializers.ValidationError({'price_per_unit': 'Price per unit is required for ad-hoc expenses.'})

        if item:
            validated_data['item_name_snapshot'] = item.name
            validated_data['unit_type_snapshot'] = item.unit_type
            validated_data['category_snapshot'] = item.category
        else:
            validated_data['item_name_snapshot'] = item_name
            validated_data['unit_type_snapshot'] = item_unit_type or 'unit'
            validated_data['category_snapshot'] = item_category

        return super().create(validated_data)
