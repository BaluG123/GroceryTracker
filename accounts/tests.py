from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class PasswordResetFlowTests(APITestCase):
    def test_forgot_password_with_security_answer_updates_password(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'maya',
            'email': 'maya@example.com',
            'password': 'InitialPass123!',
            'reset_question': 'Favourite city',
            'reset_answer': 'Delhi',
        }, format='json')
        self.assertEqual(response.status_code, 201)

        response = self.client.post('/api/auth/forgot-password/', {
            'username': 'maya',
            'reset_answer': 'Delhi',
            'new_password': 'UpdatedPass123!',
            'confirm_password': 'UpdatedPass123!',
        }, format='json')
        self.assertEqual(response.status_code, 200)

        login_response = self.client.post('/api/auth/login/', {
            'username': 'maya',
            'password': 'UpdatedPass123!',
        }, format='json')
        self.assertEqual(login_response.status_code, 200)

    def test_change_password_requires_current_password(self):
        user = User.objects.create_user(
            username='ravi',
            email='ravi@example.com',
            password='CurrentPass123!',
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.post('/api/auth/change-password/', {
            'old_password': 'wrong-pass',
            'new_password': 'BrandNewPass123!',
            'confirm_password': 'BrandNewPass123!',
        }, format='json')

        self.assertEqual(response.status_code, 400)

