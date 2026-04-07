import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key-here-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS =[
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
    'custom_admin',  # New customized dashboard app
    'rest_framework',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

# Custom Admin Configuration
# We are using a fully custom Django admin panel built locally.


SITE_ID = 1

MIDDLEWARE =[
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'myapp.middleware.AutoDowngradeMiddleware', 
]

ROOT_URLCONF = 'NepseSewa.urls'

TEMPLATES =[
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'Templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors':[
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'NepseSewa.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nepse_sewa',
        'USER': 'postgres',
        'PASSWORD': 'Adrian@2062',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Custom User Model
AUTH_USER_MODEL = 'myapp.CustomUser'

# Authentication Backends
AUTHENTICATION_BACKENDS =[
    'myapp.views.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS =[
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# ========== GOOGLE OAUTH SETTINGS ==========
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',   
            'email',     
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'VERIFIED_EMAIL': True,
        'VERSION': 'v2',
    }
}

# ========== ALLAUTH SETTINGS ==========
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'

# Store these securely in environment variables in production
SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
    'client_id': '698946278656-gcv1iunmrr66dthuquen430pfjlk57g8.apps.googleusercontent.com',
    'secret': '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',
    'key': ''
}

# CORS Settings
CORS_ALLOWED_ORIGINS =[
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'adrianpoudyal@gmail.com'  
EMAIL_HOST_PASSWORD = 'xflhaikspmcwihkh'  
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ========== INTEGRATION SETTINGS ==========
BASE_URL = "http://127.0.0.1:8000"

# ========== KHALTI INTEGRATION SETTINGS ==========
KHALTI_PUBLIC_KEY = "e62e4d9b16a84b1eb0cbd2dc24f23603"
KHALTI_SECRET_KEY = "be28940eceee4bc1b2e27d26427b869d"
KHALTI_INITIATE_URL = "https://a.khalti.com/api/v2/epayment/initiate/"
KHALTI_LOOKUP_URL = "https://a.khalti.com/api/v2/epayment/lookup/"
KHALTI_RETURN_URL = f"{BASE_URL}/payment/khalti/success/"

# ========== CELERY SETTINGS ==========
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# For development: Set this to True to run tasks synchronously without Redis
# Set to False once Redis and Celery worker are running locally
CELERY_TASK_ALWAYS_EAGER = True 

