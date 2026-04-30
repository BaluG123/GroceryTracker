"""
Root URL configuration for Daily Grocery Expense Tracker.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Auth endpoints
    path('api/auth/', include('accounts.urls')),

    # Tracker endpoints (items, purchases, reports)
    path('api/', include('tracker.urls')),

    # DRF browsable API login (optional, handy for development)
    path('api-auth/', include('rest_framework.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
