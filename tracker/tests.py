from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import GroceryItem, Purchase


class ExpenseItemTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='dev',
            email='dev@example.com',
            password='Password123!',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_item_list_is_not_paginated_and_returns_all_items(self):
        for index in range(25):
            GroceryItem.objects.create(
                user=self.user,
                name=f'Item {index}',
                unit_type='unit',
                default_price_per_unit=Decimal('10.00'),
                category='General',
            )

        response = self.client.get('/api/items/')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 25)

    def test_soft_delete_hides_item_but_preserves_purchase_history(self):
        item = GroceryItem.objects.create(
            user=self.user,
            name='Bus Ticket',
            unit_type='trip',
            default_price_per_unit=Decimal('35.00'),
            category='Transport',
        )
        purchase = Purchase.objects.create(
            user=self.user,
            item=item,
            quantity=Decimal('1.00'),
            price_per_unit=Decimal('35.00'),
            merchant_name='City Bus',
        )

        delete_response = self.client.delete(f'/api/items/{item.id}/')
        self.assertEqual(delete_response.status_code, 204)

        item.refresh_from_db()
        purchase.refresh_from_db()

        self.assertFalse(item.is_active)
        self.assertEqual(purchase.item_id, item.id)
        self.assertEqual(purchase.item_name_snapshot, 'Bus Ticket')

        list_response = self.client.get('/api/items/')
        self.assertEqual(len(list_response.data), 0)

        inactive_response = self.client.get('/api/items/?include_inactive=true')
        self.assertEqual(len(inactive_response.data), 1)

    def test_can_create_ad_hoc_expense_without_reusable_item(self):
        response = self.client.post('/api/expenses/', {
            'item_name': 'Tea',
            'item_unit_type': 'cup',
            'item_category': 'Food',
            'quantity': '2.00',
            'price_per_unit': '15.00',
            'merchant_name': 'Station Stall',
            'payment_method': 'cash',
            'currency_code': 'inr',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['item'], None)

        purchase = Purchase.objects.get()
        self.assertEqual(purchase.item_name_snapshot, 'Tea')
        self.assertEqual(purchase.currency_code, 'INR')
