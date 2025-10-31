from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'is_verified', 'is_disabled', 'user_type'),
        }),
    )
    list_display = ('username', 'email', 'role', 'is_verified', 'is_disabled', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_disabled', 'is_staff', 'is_superuser')
