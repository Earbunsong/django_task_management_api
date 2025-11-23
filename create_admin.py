#!/usr/bin/env python
"""Create admin user"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_mangement_api.settings')
django.setup()

from accounts.models import User

# Check if admin user exists
admin = User.objects.filter(username='admin').first()

if admin:
    print(f"Admin user already exists: {admin.username} ({admin.email})")
    print(f"Role: {admin.role}")
    print(f"Is superuser: {admin.is_superuser}")
    print(f"Is verified: {admin.is_verified}")
else:
    # Create admin user
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@taskmanager.com',
        password='admin123'
    )
    admin.role = 'admin'
    admin.is_verified = True
    admin.save()

    print(f"Created admin user:")
    print(f"  Username: {admin.username}")
    print(f"  Email: {admin.email}")
    print(f"  Password: admin123")
    print(f"  Role: {admin.role}")
    print(f"  Is superuser: {admin.is_superuser}")
    print(f"  Is verified: {admin.is_verified}")
