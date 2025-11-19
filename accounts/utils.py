"""Utility functions for accounts app"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Token generator for email verification"""

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_verified}"


email_verification_token = EmailVerificationTokenGenerator()
password_reset_token = PasswordResetTokenGenerator()


def send_verification_email(user, request=None):
    """
    Send email verification link to user

    Args:
        user: User instance
        request: HTTP request object (optional, for building absolute URL)

    Returns:
        bool: True if email sent successfully
    """
    try:
        # Generate token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)

        # Build verification URL
        if request:
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
        else:
            domain = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'localhost:3000'
            protocol = 'http'

        verification_url = f"{protocol}://{domain}/api/v1/auth/verify/{uid}/{token}/"

        # Email content
        subject = 'Verify Your Email - Task Management System'
        message = f"""
        Hi {user.username},

        Thank you for registering with Task Management System!

        Please click the link below to verify your email address:
        {verification_url}

        This link will expire in 24 hours.

        If you didn't create an account, please ignore this email.

        Best regards,
        Task Management Team
        """

        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); padding: 40px 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Welcome to Task Management!</h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px; color: #333333; font-size: 16px; line-height: 1.6;">
                                Hi <strong>{user.username}</strong>,
                            </p>

                            <p style="margin: 0 0 20px; color: #555555; font-size: 15px; line-height: 1.6;">
                                Thank you for registering with Task Management System! We're excited to have you on board.
                            </p>

                            <p style="margin: 0 0 20px; color: #555555; font-size: 15px; line-height: 1.6;">
                                To get started, please verify your email address by clicking the button below:
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" style="margin: 30px 0;">
                                <tr>
                                    <td style="text-align: center;">
                                        <a href="{verification_url}"
                                           style="display: inline-block; background-color: #4CAF50; color: #ffffff;
                                                  padding: 14px 40px; text-decoration: none; border-radius: 6px;
                                                  font-weight: 600; font-size: 16px; box-shadow: 0 2px 4px rgba(76,175,80,0.4);">
                                            Verify Email Address
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 30px 0 20px; color: #666666; font-size: 14px; line-height: 1.6;">
                                Or copy and paste this link into your browser:
                            </p>

                            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #4CAF50; margin-bottom: 30px;">
                                <code style="color: #4CAF50; font-size: 12px; word-break: break-all; display: block;">{verification_url}</code>
                            </div>

                            <!-- Info Box -->
                            <div style="background-color: #e8f5e9; border-left: 4px solid #4CAF50; padding: 15px; border-radius: 4px; margin: 20px 0;">
                                <p style="margin: 0 0 10px; color: #2e7d32; font-size: 14px; font-weight: 600;">
                                    ✨ What's Next?
                                </p>
                                <ul style="margin: 0; padding-left: 20px; color: #2e7d32; font-size: 13px; line-height: 1.6;">
                                    <li>Verify your email to unlock all features</li>
                                    <li>Create and manage tasks efficiently</li>
                                    <li>Collaborate with your team</li>
                                    <li>Track your progress in real-time</li>
                                </ul>
                            </div>

                            <p style="margin: 20px 0 0; color: #999999; font-size: 13px; line-height: 1.6;">
                                <small>This link will expire in 24 hours.</small>
                            </p>

                            <p style="margin: 10px 0 0; color: #999999; font-size: 14px; line-height: 1.6;">
                                If you didn't create an account, please ignore this email.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-radius: 0 0 8px 8px; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0 0 10px; color: #6c757d; font-size: 14px;">
                                Best regards,<br>
                                <strong>Task Management Team</strong>
                            </p>
                            <p style="margin: 10px 0 0; color: #999999; font-size: 12px;">
                                This is an automated message, please do not reply to this email.
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- Footer Text -->
                <table role="presentation" style="max-width: 600px; margin: 20px auto 0;">
                    <tr>
                        <td style="text-align: center; padding: 20px;">
                            <p style="margin: 0; color: #999999; font-size: 12px;">
                                © 2025 Task Management System. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Verification email sent to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, request=None):
    """
    Send password reset link to user

    Args:
        user: User instance
        request: HTTP request object (optional)

    Returns:
        bool: True if email sent successfully
    """
    try:
        # Generate token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)

        # Build reset URL
        # Format: FRONTEND_URL/reset-password?uid=XXX&token=YYY
        # Works for both web (http://localhost) and mobile (taskmanager://)
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        reset_url = f"{frontend_url}/reset-password?uid={uid}&token={token}"

        # Email content
        subject = 'Password Reset Request - Task Management System'
        message = f"""
Hi {user.username},

We received a request to reset your password for your Task Management System account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email or contact support if you have concerns.

For security reasons, please note:
- We will never ask for your password via email
- This link can only be used once
- If you didn't request this reset, your account is still secure

Best regards,
Task Management Team
        """

        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%); padding: 40px 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Password Reset Request</h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px; color: #333333; font-size: 16px; line-height: 1.6;">
                                Hi <strong>{user.username}</strong>,
                            </p>

                            <p style="margin: 0 0 20px; color: #555555; font-size: 15px; line-height: 1.6;">
                                We received a request to reset your password for your Task Management System account. Click the button below to create a new password:
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" style="margin: 30px 0;">
                                <tr>
                                    <td style="text-align: center;">
                                        <a href="{reset_url}"
                                           style="display: inline-block; background-color: #1976D2; color: #ffffff;
                                                  padding: 14px 40px; text-decoration: none; border-radius: 6px;
                                                  font-weight: 600; font-size: 16px; box-shadow: 0 2px 4px rgba(25,118,210,0.4);">
                                            Reset Your Password
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 30px 0 20px; color: #666666; font-size: 14px; line-height: 1.6;">
                                Or copy and paste this link into your mobile app or browser:
                            </p>

                            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #1976D2; margin-bottom: 30px;">
                                <code style="color: #1976D2; font-size: 12px; word-break: break-all; display: block;">{reset_url}</code>
                            </div>

                            <!-- Security Notice -->
                            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 4px; margin: 20px 0;">
                                <p style="margin: 0 0 10px; color: #856404; font-size: 14px; font-weight: 600;">
                                    🔒 Security Information
                                </p>
                                <ul style="margin: 0; padding-left: 20px; color: #856404; font-size: 13px; line-height: 1.6;">
                                    <li>This link will expire in <strong>1 hour</strong></li>
                                    <li>This link can only be used <strong>once</strong></li>
                                    <li>We will never ask for your password via email</li>
                                </ul>
                            </div>

                            <p style="margin: 20px 0 0; color: #999999; font-size: 14px; line-height: 1.6;">
                                If you didn't request a password reset, please ignore this email or contact support if you have concerns. Your account is still secure.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-radius: 0 0 8px 8px; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0 0 10px; color: #6c757d; font-size: 14px;">
                                Best regards,<br>
                                <strong>Task Management Team</strong>
                            </p>
                            <p style="margin: 10px 0 0; color: #999999; font-size: 12px;">
                                This is an automated message, please do not reply to this email.
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- Footer Text -->
                <table role="presentation" style="max-width: 600px; margin: 20px auto 0;">
                    <tr>
                        <td style="text-align: center; padding: 20px;">
                            <p style="margin: 0; color: #999999; font-size: 12px;">
                                © 2025 Task Management System. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Password reset email sent to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def verify_email_token(uidb64, token):
    """
    Verify email verification token

    Args:
        uidb64: Base64 encoded user ID
        token: Verification token

    Returns:
        User instance if valid, None otherwise
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        if email_verification_token.check_token(user, token):
            return user
        return None

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def verify_password_reset_token(uidb64, token):
    """
    Verify password reset token

    Args:
        uidb64: Base64 encoded user ID
        token: Reset token

    Returns:
        User instance if valid, None otherwise
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        if password_reset_token.check_token(user, token):
            return user
        return None

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
