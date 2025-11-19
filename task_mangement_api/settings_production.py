"""
Production settings for Task Management API
Import this instead of settings.py in production:
Set environment variable: DJANGO_SETTINGS_MODULE=task_mangement_api.settings_production
"""

from .settings import *
import os

# Override development settings for production

# Security Settings
DEBUG = False

# Must be set in environment
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError("ALLOWED_HOSTS must be set in production")

# Security Headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database - Ensure PostgreSQL is used
if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    raise ValueError("SQLite is not allowed in production. Use PostgreSQL.")

# Static Files with WhiteNoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Email - Must use SMTP backend in production
if EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Validate required environment variables
required_env_vars = [
    'SECRET_KEY',
    'POSTGRES_DB',
    'POSTGRES_USER',
    'POSTGRES_PASSWORD',
    'STRIPE_SECRET_KEY',
]

for var in required_env_vars:
    if not os.environ.get(var):
        raise ValueError(f"Required environment variable {var} is not set")

# CORS - Restrict origins in production
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
if not CORS_ALLOWED_ORIGINS or CORS_ALLOWED_ORIGINS == ['']:
    raise ValueError("CORS_ALLOWED_ORIGINS must be set in production")

# Logging - File-based logging in production
LOGGING['handlers']['file']['filename'] = '/var/log/django/task_manager.log'

# Cache Configuration - Use Redis in production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'task_manager',
        'TIMEOUT': 300,
    }
}

# Session cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Admin Security
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')  # Use custom admin URL

# Rate limiting - More strict in production
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '50/hour',
    'user': '500/hour'
}
