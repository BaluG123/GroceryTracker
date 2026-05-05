"""
Serializers for user registration and login.
"""

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import AccountSecurityProfile


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles new user registration.
    Accepts username, email, password, first_name, last_name.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True)
    reset_question = serializers.CharField(write_only=True, required=False, allow_blank=True)
    reset_answer = serializers.CharField(write_only=True, required=False, allow_blank=True, trim_whitespace=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'reset_question', 'reset_answer',
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        reset_question = validated_data.pop('reset_question', '').strip()
        reset_answer = validated_data.pop('reset_answer', '').strip()
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        if reset_question or reset_answer:
            AccountSecurityProfile.objects.create(
                user=user,
                reset_question=reset_question,
                reset_answer_hash=make_password(reset_answer.lower()) if reset_answer else '',
            )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Validates login credentials and returns the authenticated user.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for returning user profile info.
    """
    reset_question = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'date_joined', 'reset_question',
        ]
        read_only_fields = fields

    def get_reset_question(self, obj):
        profile = getattr(obj, 'security_profile', None)
        return profile.reset_question if profile and profile.reset_question else ''


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'Old password is incorrect.'})
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        validate_password(attrs['new_password'], user=user)
        return attrs


class ConfigureResetSerializer(serializers.Serializer):
    reset_question = serializers.CharField(max_length=255)
    reset_answer = serializers.CharField(write_only=True, trim_whitespace=True, min_length=3)

    def save(self, **kwargs):
        user = self.context['request'].user
        profile, _ = AccountSecurityProfile.objects.get_or_create(user=user)
        profile.reset_question = self.validated_data['reset_question'].strip()
        profile.reset_answer_hash = make_password(self.validated_data['reset_answer'].strip().lower())
        profile.save(update_fields=['reset_question', 'reset_answer_hash', 'updated_at'])
        return profile


class ForgotPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    reset_answer = serializers.CharField(write_only=True, trim_whitespace=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})

        try:
            user = User.objects.get(username=attrs['username'])
        except User.DoesNotExist as exc:
            raise serializers.ValidationError({'username': 'User not found.'}) from exc

        profile = getattr(user, 'security_profile', None)
        if not profile or not profile.reset_answer_hash:
            raise serializers.ValidationError({'username': 'Password reset is not configured for this account.'})
        if not check_password(attrs['reset_answer'].strip().lower(), profile.reset_answer_hash):
            raise serializers.ValidationError({'reset_answer': 'Reset answer is incorrect.'})

        validate_password(attrs['new_password'], user=user)
        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user
