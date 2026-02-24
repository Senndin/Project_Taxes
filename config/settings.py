import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-fallback-key-for-build')
DEBUG = env('DEBUG', default=False)

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    
    # Local apps
    'tax_service',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'frontend', 'dist')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=env('DATABASE_URL', default='sqlite:///db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'

# WhiteNoise configuration to serve React static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# React outputs build into frontend/dist. 
# We serve this directory at the root level using WHITENOISE_ROOT so /assets/... works natively.
WHITENOISE_ROOT = os.path.join(BASE_DIR, 'frontend', 'dist')
STATICFILES_DIRS = []

# Tell WhiteNoise to serve React index.html for root path implicitly if we don't catch it
WHITENOISE_INDEX_FILE = True


# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'tax_service.pagination.StandardResultsSetPagination',
}

# Celery settings
red_url = env('REDIS_URL', default='redis://localhost:6379/1')

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default=env('REDIS_URL', default='redis://localhost:6379/0'))
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=env('REDIS_URL', default='redis://localhost:6379/1'))

import ssl
if CELERY_BROKER_URL.startswith('rediss://'):
    CELERY_BROKER_USE_SSL = {'ssl_cert_reqs': ssl.CERT_NONE}
if CELERY_RESULT_BACKEND.startswith('rediss://'):
    CELERY_REDIS_BACKEND_USE_SSL = {'ssl_cert_reqs': ssl.CERT_NONE}

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
