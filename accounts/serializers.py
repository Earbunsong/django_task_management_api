from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }

    def validate_email(self, value):
        """Check if email is already registered"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """Check if username is already taken"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        try:
            validate_password(password, user)
        except Exception as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'is_disabled')
        read_only_fields = ('role', 'is_verified', 'is_disabled', 'id')


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that accepts email instead of username"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the username field and add email field
        if 'username' in self.fields:
            del self.fields['username']
        self.fields['email'] = serializers.EmailField(required=True)

    def validate(self, attrs):
        # Get email and password from request
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Email and password are required.')

        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('No active account found with the given credentials.')

        # Log user verification status for debugging
        logger.info(f"Login attempt for user {user.username} (email: {email})")
        logger.info(f"User verification status: is_verified={user.is_verified}, is_active={user.is_active}, is_disabled={user.is_disabled}")

        # Check if account is disabled
        if user.is_disabled or not user.is_active:
            logger.warning(f"Login blocked for disabled user: {email}")
            raise serializers.ValidationError({
                'account_disabled': True,
                'email': email,
                'message': 'Your account has been disabled by an administrator. Please contact support for assistance.'
            })

        # Check if email is verified
        if not user.is_verified:
            logger.warning(f"Login blocked for unverified user: {email}")
            raise serializers.ValidationError({
                'email_not_verified': True,
                'email': email,
                'message': 'Please verify your email before logging in. Check your inbox for the verification link.'
            })

        # Add username to attrs for parent validation
        attrs['username'] = user.username

        logger.info(f"User {user.username} passed verification check, proceeding with authentication")

        # Call parent validate
        return super().validate(attrs)
