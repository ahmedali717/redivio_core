"""
Django settings for redivio_project project.
"""

import os
import sys
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = "django-insecure-change-this-in-production"
DEBUG = True # حولها لـ False عند الانتهاء تماماً
ALLOWED_HOSTS = ["ahmedali717.pythonanywhere.com", "localhost", "127.0.0.1"]

# ضروري جداً لعمل الـ Vue.js مع السيرفر الجديد
CSRF_TRUSTED_ORIGINS = [
    "https://ahmedali717.pythonanywhere.com",
    "http://localhost:8000",
]

# إجبار جانغو على وضع / في نهاية الروابط
APPEND_SLASH = True

# =========================================================
# INSTALLED APPS
# =========================================================

INSTALLED_APPS = [
    "jazzmin",

    # Core
    "apps.core",

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third Party
    "rest_framework",
    "corsheaders",

    # Business Apps
    "apps.item_master",
    "apps.wms",
    "apps.procurement",
    "apps.sales",
]

# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # ✅ Tenant Resolver (your middleware)
    "apps.core.middleware.TenantMiddleware",
]

ROOT_URLCONF = "redivio_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "redivio_project.wsgi.application"

# =========================================================
# DATABASE (Neon / PostgreSQL)
# =========================================================

DATABASE_URL = "postgresql://neondb_owner:npg_KrNedg5V2ThF@ep-broad-tooth-adixzfhp-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =========================================================
# STATIC & MEDIA
# =========================================================

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# نستخدم التخزين العادي لتجنب مشاكل الملفات الناقصة في Whitenoise
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False

STATICFILES_DIRS = [
    BASE_DIR / "redivio_project/static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================================================
# CORS
# =========================================================

CORS_ALLOW_ALL_ORIGINS = True

# =========================================================
# REST FRAMEWORK
# =========================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# =========================================================
# GOOGLE LOGIN (Optional)
# =========================================================

GOOGLE_CLIENT_ID = "your-google-client-id"

# =========================================================
# JAZZMIN (Admin UI Branding)
# =========================================================

JAZZMIN_SETTINGS = {
    "site_title": "Redivio ERP",
    "site_header": "Redivio",
    "site_brand": "REDIVIO",
    "site_logo": "brand/logo_r.png",
    "login_logo": "brand/logo_r.png",
    "search_model": ["item_master.Material", "sales.SalesOrder", "procurement.PurchaseOrder"],
    "order_with_respect_to": ["core", "item_master", "wms", "procurement", "sales"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "core.OpCo": "fas fa-building",
        "item_master.Material": "fas fa-box-open",
        "wms.Plant": "fas fa-warehouse",
        "wms.StockQuant": "fas fa-cubes",
        "procurement.PurchaseOrder": "fas fa-shopping-cart",
        "procurement.Vendor": "fas fa-truck",
        "sales.SalesOrder": "fas fa-file-invoice-dollar",
        "sales.Customer": "fas fa-users",
    },
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-dark navbar-black",
    "sidebar": "sidebar-dark-black",
    "theme": "flatly",
    "button_classes": {
        "primary": "btn-dark",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

# =========================================================
# SECURITY HEADERS (Fix for Vue.js Block issues)
# =========================================================

# السماح للـ Vue.js بتنفيذ العمليات الحسابية (eval) داخل المتصفح
# ده هيحل مشكلة "Content Security Policy blocks the use of eval"
CSP_DEFAULT_SRC = ("'self'", "https://unpkg.com", "https://cdnjs.cloudflare.com")
CSP_SCRIPT_SRC = (
    "'self'", 
    "https://unpkg.com", 
    "https://cdnjs.cloudflare.com", 
    "'unsafe-inline'", 
    "'unsafe-eval'"  # السطر ده هو اللي هيخلي الـ Vue يشتغل
)
CSP_STYLE_SRC = ("'self'", "https://fonts.googleapis.com", "https://cdnjs.cloudflare.com", "https://unpkg.com", "'unsafe-inline'")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com")

# إيقاف الحماية الصارمة لنوع المحتوى مؤقتاً لضمان تحميل المكتبات
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = "SAMEORIGIN"