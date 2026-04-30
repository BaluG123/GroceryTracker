"""
Auth views: Register, Login (get token), Logout (delete token), Profile.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


@extend_schema(
    request=RegisterSerializer,
    responses={201: UserSerializer},
    description="Register a new user account.",
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Create a new user and return an auth token."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {
            'message': 'Registration successful.',
            'token': token.key,
            'user': UserSerializer(user).data,
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    request=LoginSerializer,
    responses={200: UserSerializer},
    description="Login with username & password to receive an auth token.",
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate and return an auth token."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {
            'message': 'Login successful.',
            'token': token.key,
            'user': UserSerializer(user).data,
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(
    responses={200: None},
    description="Logout — invalidates the current auth token.",
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Delete the user's auth token to log them out."""
    request.user.auth_token.delete()
    return Response(
        {'message': 'Logged out successfully.'},
        status=status.HTTP_200_OK,
    )


@extend_schema(
    responses={200: UserSerializer},
    description="Get the authenticated user's profile.",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """Return the authenticated user's profile."""
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
