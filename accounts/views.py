from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, UserSerializer
from .utils import send_verification_email, verify_email_token
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class AllowAnyForAuth(permissions.AllowAny):
    pass


class RegisterView(APIView):
    permission_classes = [AllowAnyForAuth]

    def post(self, request):
        logger.info(f"Registration attempt with data: {request.data.keys()}")

        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Registration validation failed: {serializer.errors}")
            return Response({
                "errors": serializer.errors,
                "message": "Registration failed. Please check the errors below."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            logger.info(f"User {user.username} created successfully.")
        except serializers.ValidationError as e:
            # Handle password validation errors properly
            logger.error(f"Registration validation failed during save: {e.detail}")
            return Response({
                "errors": e.detail,
                "message": "Registration failed. Please check the errors below."
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return Response({
                "message": "Failed to create user account.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Send verification email
        try:
            send_verification_email(user, request)
            logger.info(f"User {user.username} registered successfully. Verification email sent.")
            return Response({
                "message": "Registered successfully. Please check your email to verify your account.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return Response({
                "message": "Registered successfully, but failed to send verification email. Please contact support.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAnyForAuth]

    def get(self, request, uidb64: str, token: str):
        """Verify email using token from email link"""
        user = verify_email_token(uidb64, token)

        if user is None:
            return Response({
                "detail": "Invalid or expired verification link."
            }, status=status.HTTP_400_BAD_REQUEST)

        if user.is_verified:
            return Response({
                "message": "Email already verified. You can log in now."
            }, status=status.HTTP_200_OK)

        # Mark user as verified
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        logger.info(f"User {user.username} email verified successfully.")

        return Response({
            "message": "Email verified successfully! You can now log in."
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        # With JWT this is typically handled client-side or via blacklist; stubbed
        return Response(status=status.HTTP_204_NO_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAnyForAuth]

    def post(self, request):
        """Send password reset email"""
        from .utils import send_password_reset_email

        email = request.data.get('email')
        if not email:
            return Response({
                "detail": "Email is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            # Send reset email
            if send_password_reset_email(user, request):
                logger.info(f"Password reset email sent to {email}")
                return Response({
                    "message": "If an account with that email exists, a password reset link has been sent."
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "detail": "Failed to send reset email. Please try again later."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            return Response({
                "message": "If an account with that email exists, a password reset link has been sent."
            }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [AllowAnyForAuth]

    def post(self, request):
        """Reset password using token from email"""
        from .utils import verify_password_reset_token

        uidb64 = request.data.get('uidb64')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not all([uidb64, token, new_password]):
            return Response({
                "detail": "uidb64, token, and new_password are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate password strength
        if len(new_password) < 8:
            return Response({
                "detail": "Password must be at least 8 characters long."
            }, status=status.HTTP_400_BAD_REQUEST)

        user = verify_password_reset_token(uidb64, token)

        if user is None:
            return Response({
                "detail": "Invalid or expired reset link."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(new_password)
        user.save()
        logger.info(f"Password reset successfully for user {user.username}")

        return Response({
            "message": "Password reset successfully. You can now log in with your new password."
        }, status=status.HTTP_200_OK)


class ProfileView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminDisableUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk: int):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.is_disabled = True
        user.is_active = False
        user.save(update_fields=["is_disabled", "is_active"])

        # Send notification to user
        try:
            from notifications.fcm_utils import send_account_status_notification
            from notifications.models import Notification

            send_account_status_notification(user, is_disabled=True)
            Notification.objects.create(
                user=user,
                message="Your account has been disabled. Please contact support for assistance."
            )
        except Exception as e:
            logger.error(f"Failed to send account status notification: {str(e)}")

        return Response({"message": "User disabled"}, status=status.HTTP_200_OK)
