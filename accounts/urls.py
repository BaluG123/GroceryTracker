"""
URL routes for authentication.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='auth-register'),
    path('login/', views.login_view, name='auth-login'),
    path('logout/', views.logout_view, name='auth-logout'),
    path('profile/', views.profile_view, name='auth-profile'),
    path('configure-reset/', views.configure_reset_view, name='auth-configure-reset'),
    path('forgot-password/', views.forgot_password_view, name='auth-forgot-password'),
    path('change-password/', views.change_password_view, name='auth-change-password'),
]
