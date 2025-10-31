from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        BASIC = 'basic', 'Basic User'
        PRO = 'pro', 'Pro User'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BASIC)
    user_type = models.CharField(max_length=10, choices=Role.choices, default=Role.BASIC)
    is_verified = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)

    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_pro(self):
        return self.role == self.Role.PRO
