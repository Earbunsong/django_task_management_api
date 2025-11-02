from django.conf import settings
from django.db import models


class Subscription(models.Model):
    class PlanType(models.TextChoices):
        BASIC = 'basic', 'Basic'
        PRO = 'pro', 'Pro'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=10, choices=PlanType.choices, default=PlanType.BASIC, db_index=True)
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    payment_status = models.CharField(max_length=20, default='inactive', db_index=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, unique=True, db_index=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['payment_status', 'end_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_plan_type_display()}"


class PaymentTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments', db_index=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='usd')
    status = models.CharField(max_length=50, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.amount} {self.currency}"
