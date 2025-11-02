from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        BASIC = 'basic', 'Basic User'
        PRO = 'pro', 'Pro User'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BASIC, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    is_disabled = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['email', 'is_verified']),
            models.Index(fields=['role', 'is_active']),
        ]

    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_pro(self):
        return self.role == self.Role.PRO

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
