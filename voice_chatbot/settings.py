"""
Django settings for voice_chatbot project.
"""

from pathlib import Path
import os
import json

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load secrets from secrets.json (check multiple paths for Cloud Run)
SECRETS = {}
for _secrets_path in [BASE_DIR / 'secrets.json', Path('/secrets/secrets.json')]:
    try:
        if _secrets_path.exists():
            with open(_secrets_path, 'r') as f:
                SECRETS = json.load(f)
            break
    except Exception:
        continue
if not SECRETS:
    print("Warning: secrets.json not found. Using environment variables.")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRETS.get('SECRET_KEY') or os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = SECRETS.get('DEBUG', os.environ.get('DEBUG', 'True')) == True or os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = SECRETS.get('ALLOWED_HOSTS', os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1'))
if isinstance(ALLOWED_HOSTS, str):
    ALLOWED_HOSTS = ALLOWED_HOSTS.split(',')

# Cloud Run sets this; allow all *.run.app domains
if os.environ.get('K_SERVICE'):
    ALLOWED_HOSTS = ['*']
    DEBUG = False


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'consumers',
    'models',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'voice_chatbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'voice_chatbot.wsgi.application'
ASGI_APPLICATION = 'voice_chatbot.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Channel layers configuration
# For development, use in-memory channel layer (no Redis required)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# For production with Redis, uncomment below:
# REDIS_HOST = SECRETS.get('REDIS_HOST', '127.0.0.1')
# REDIS_PORT = SECRETS.get('REDIS_PORT', 6379)
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [(REDIS_HOST, REDIS_PORT)],
#         },
#     },
# }

# Gemini API Configuration
GEMINI_API_KEY = SECRETS.get('GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY', '')

# JWT Configuration
JWT_SECRET_KEY = SECRETS.get('JWT_SECRET_KEY') or os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
JWT_ALGORITHM = SECRETS.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = SECRETS.get('JWT_EXPIRATION_HOURS', 24)

# CORS Configuration
CORS_ALLOWED_ORIGINS = SECRETS.get('CORS_ALLOWED_ORIGINS', os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000'))
if isinstance(CORS_ALLOWED_ORIGINS, str):
    CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS.split(',')

