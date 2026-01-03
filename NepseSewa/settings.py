import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key-here-change-in-production'

DEBUG = True

ALLOWED_HOSTS = []


INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',  
    'rest_framework',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

# Unfold Admin Configuration
UNFOLD = {
    "SITE_TITLE": "NepseSewa Admin",
    "SITE_HEADER": "NepseSewa Trading Engine",
    "SITE_URL": "/",
    "DASHBOARD_CALLBACK": "myapp.admin_views.dashboard_callback",  # Optional: For custom dashboard metrics
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Trading Operations",
                "separator": True,
                "items": [
                    {
                        "title": "Trading Dashboard",
                        "icon": "bar_chart",  # Material Icon
                        "link": "admin_trading_dashboard", # URL Name
                    },
                    {
                        "title": "Orders",
                        "icon": "list_alt",
                        "link": "admin:myapp_order_changelist",
                    },
                    {
                        "title": "Executions",
                        "icon": "receipt_long",
                        "link": "admin:myapp_tradeexecution_changelist",
                    },
                ],
            },
        ],
    },
}
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'NepseSewa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'Templates'],
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
AUTHENTICATION_BACKENDS = [
    'myapp.views.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Password validation
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
# Skip intermediate pages and go directly to Google login
SOCIALACCOUNT_LOGIN_ON_GET = True

# Auto-create user accounts on social login
SOCIALACCOUNT_AUTO_SIGNUP = True

# Allow login with email or username
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_UNIQUE_EMAIL = True

# Email verification (optional - no verification needed)
ACCOUNT_EMAIL_VERIFICATION = 'optional'

# Redirect after signup
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'

# Prevent showing allauth's default signup page
ACCOUNT_SIGNUP_FIELDS = ['email']

# ========== OPTIONAL: Google OAuth Credentials ==========
# Store these securely in environment variables in production
SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
    'client_id': '698946278656-gcv1iunmrr66dthuquen430pfjlk57g8.apps.googleusercontent.com',
    'secret': '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',
    'key': ''
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}






# Email Configuration (Development - Saves to 'emails' folder)
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
# EMAIL_FILE_PATH = BASE_DIR / "emails"

# Email Configuration (Production/Real Emails)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# You must generate an App Password for this to work: https://myaccount.google.com/apppasswords
EMAIL_HOST_USER = 'adrianpoudyal@gmail.com'  # Replace with your actual Gmail
EMAIL_HOST_PASSWORD = 'rdrbpwoygnadghxs'  # The 16-character code from Google
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER




