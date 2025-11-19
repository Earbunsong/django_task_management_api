"""Firebase Cloud Messaging (FCM) utilities for push notifications"""
import logging
import os
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

# Firebase Admin SDK imports (optional, will be imported if available)
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("firebase-admin not installed. Push notifications will not work.")


# Initialize Firebase (singleton pattern)
_firebase_initialized = False


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global _firebase_initialized

    if _firebase_initialized:
        return True

    if not FIREBASE_AVAILABLE:
        logger.error("Firebase Admin SDK not installed. Run: pip install firebase-admin")
        return False

    if not settings.FIREBASE_CREDENTIALS_PATH:
        logger.warning("FIREBASE_CREDENTIALS_PATH not configured. Push notifications disabled.")
        return False

    if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        logger.error(f"Firebase credentials file not found: {settings.FIREBASE_CREDENTIALS_PATH}")
        return False

    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        return False


def send_push_notification(user, title, body, data=None):
    """
    Send push notification to a specific user

    Args:
        user: User instance or user ID
        title: Notification title
        body: Notification body
        data: Optional dictionary of additional data

    Returns:
        bool: True if notification sent successfully
    """
    if not FIREBASE_AVAILABLE:
        logger.warning("Firebase not available. Skipping push notification.")
        return False

    if not initialize_firebase():
        return False

    from .models import DeviceToken

    # Get user instance if ID provided
    if isinstance(user, int):
        try:
            user = User.objects.get(id=user)
        except User.DoesNotExist:
            logger.error(f"User with ID {user} not found")
            return False

    # Get all device tokens for the user
    tokens = DeviceToken.objects.filter(user=user).values_list('token', flat=True)

    if not tokens:
        logger.warning(f"No device tokens found for user {user.username}")
        return False

    # Prepare notification message
    notification = messaging.Notification(
        title=title,
        body=body
    )

    # Prepare data payload
    if data is None:
        data = {}
    data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

    success_count = 0
    invalid_tokens = []

    # Send to each device token
    for token in tokens:
        try:
            message = messaging.Message(
                notification=notification,
                data=data,
                token=token,
            )

            response = messaging.send(message)
            logger.info(f"Push notification sent successfully: {response}")
            success_count += 1

        except messaging.UnregisteredError:
            logger.warning(f"Invalid token, removing: {token}")
            invalid_tokens.append(token)

        except Exception as e:
            logger.error(f"Failed to send push notification to token {token}: {str(e)}")

    # Remove invalid tokens
    if invalid_tokens:
        DeviceToken.objects.filter(token__in=invalid_tokens).delete()
        logger.info(f"Removed {len(invalid_tokens)} invalid device tokens")

    return success_count > 0


def send_push_notification_multicast(user_ids, title, body, data=None):
    """
    Send push notification to multiple users

    Args:
        user_ids: List of user IDs
        title: Notification title
        body: Notification body
        data: Optional dictionary of additional data

    Returns:
        int: Number of successful sends
    """
    if not FIREBASE_AVAILABLE:
        logger.warning("Firebase not available. Skipping push notifications.")
        return 0

    if not initialize_firebase():
        return 0

    from .models import DeviceToken

    # Get all device tokens for the users
    tokens = list(DeviceToken.objects.filter(user_id__in=user_ids).values_list('token', flat=True))

    if not tokens:
        logger.warning(f"No device tokens found for {len(user_ids)} users")
        return 0

    # Prepare notification
    notification = messaging.Notification(
        title=title,
        body=body
    )

    # Prepare data payload
    if data is None:
        data = {}
    data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

    try:
        # Send multicast message
        message = messaging.MulticastMessage(
            notification=notification,
            data=data,
            tokens=tokens,
        )

        response = messaging.send_multicast(message)
        logger.info(f"Multicast notification sent. Success: {response.success_count}, Failure: {response.failure_count}")

        # Handle failed tokens
        if response.failure_count > 0:
            failed_tokens = []
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failed_tokens.append(tokens[idx])
                    logger.error(f"Failed to send to token: {resp.exception}")

            # Remove invalid tokens
            if failed_tokens:
                DeviceToken.objects.filter(token__in=failed_tokens).delete()
                logger.info(f"Removed {len(failed_tokens)} invalid device tokens")

        return response.success_count

    except Exception as e:
        logger.error(f"Failed to send multicast notification: {str(e)}")
        return 0


def send_task_assignment_notification(task, assigned_to_user):
    """
    Send notification when a task is assigned

    Args:
        task: Task instance
        assigned_to_user: User instance who was assigned the task

    Returns:
        bool: True if notification sent successfully
    """
    title = "New Task Assigned"
    body = f"You've been assigned to task: {task.title}"
    data = {
        'type': 'task_assignment',
        'task_id': str(task.id),
        'task_title': task.title,
    }

    return send_push_notification(assigned_to_user, title, body, data)


def send_task_update_notification(task, users):
    """
    Send notification when a task is updated

    Args:
        task: Task instance
        users: List of User instances to notify

    Returns:
        int: Number of successful sends
    """
    title = "Task Updated"
    body = f"Task '{task.title}' has been updated"
    data = {
        'type': 'task_update',
        'task_id': str(task.id),
        'task_title': task.title,
        'task_status': task.status,
    }

    user_ids = [user.id for user in users]
    return send_push_notification_multicast(user_ids, title, body, data)


def send_payment_success_notification(user, amount, currency='USD'):
    """
    Send notification when payment is successful

    Args:
        user: User instance
        amount: Payment amount
        currency: Currency code

    Returns:
        bool: True if notification sent successfully
    """
    title = "Payment Successful"
    body = f"Your payment of {currency} {amount} was processed successfully. Welcome to Pro!"
    data = {
        'type': 'payment_success',
        'amount': str(amount),
        'currency': currency,
    }

    return send_push_notification(user, title, body, data)


def send_account_status_notification(user, is_disabled):
    """
    Send notification when account status changes

    Args:
        user: User instance
        is_disabled: Boolean indicating if account is disabled

    Returns:
        bool: True if notification sent successfully
    """
    if is_disabled:
        title = "Account Disabled"
        body = "Your account has been disabled. Please contact support for assistance."
    else:
        title = "Account Reactivated"
        body = "Your account has been reactivated. Welcome back!"

    data = {
        'type': 'account_status',
        'is_disabled': str(is_disabled),
    }

    return send_push_notification(user, title, body, data)


def send_registration_notification(user):
    """
    Send notification after user registration

    Args:
        user: User instance

    Returns:
        bool: True if notification sent successfully
    """
    title = "Welcome to Task Manager!"
    body = f"Hi {user.username}! Please verify your email to unlock all features."
    data = {
        'type': 'registration',
        'user_id': str(user.id),
    }

    return send_push_notification(user, title, body, data)


def send_email_verification_success_notification(user):
    """
    Send notification when email is successfully verified

    Args:
        user: User instance

    Returns:
        bool: True if notification sent successfully
    """
    title = "Email Verified!"
    body = "Your email has been verified successfully. You now have full access to all features."
    data = {
        'type': 'email_verified',
        'user_id': str(user.id),
    }

    return send_push_notification(user, title, body, data)


def send_password_reset_requested_notification(user):
    """
    Send notification when password reset is requested

    Args:
        user: User instance

    Returns:
        bool: True if notification sent successfully
    """
    title = "Password Reset Requested"
    body = "We received a request to reset your password. Check your email for instructions."
    data = {
        'type': 'password_reset_requested',
        'user_id': str(user.id),
    }

    return send_push_notification(user, title, body, data)


def send_password_reset_success_notification(user):
    """
    Send notification when password is successfully reset

    Args:
        user: User instance

    Returns:
        bool: True if notification sent successfully
    """
    title = "Password Reset Successful"
    body = "Your password has been changed successfully. You can now log in with your new password."
    data = {
        'type': 'password_reset_success',
        'user_id': str(user.id),
    }

    return send_push_notification(user, title, body, data)
