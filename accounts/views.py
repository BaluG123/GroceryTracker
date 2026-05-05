"""
Auth views: Register, Login (get token), Logout (delete token), Profile.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema

from .serializers import (
    ChangePasswordSerializer,
    ConfigureResetSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)


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


@extend_schema(
    request=ConfigureResetSerializer,
    responses={200: None},
    description="Configure or update the local password reset question and answer.",
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def configure_reset_view(request):
    serializer = ConfigureResetSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({'message': 'Password reset configuration updated.'}, status=status.HTTP_200_OK)


@extend_schema(
    request=ForgotPasswordSerializer,
    responses={200: None},
    description="Reset a password locally using username and the configured reset answer.",
)
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    Token.objects.filter(user=serializer.validated_data['user']).delete()
    return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)


@extend_schema(
    request=ChangePasswordSerializer,
    responses={200: None},
    description="Change the authenticated user's password using the current password.",
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save(update_fields=['password'])
    Token.objects.filter(user=request.user).exclude(key=request.auth.key if request.auth else None).delete()
    return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
