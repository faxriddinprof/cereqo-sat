import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

PUBLIC_TUNNEL = os.environ.get("CEREQO_PUBLIC_TUNNEL", "0") == "1"

SECRET_KEY = os.environ.get("CEREQO_SECRET_KEY", "django-insecure-cereqo-local-demo-only")
if PUBLIC_TUNNEL and "CEREQO_SECRET_KEY" not in os.environ:
    raise ImproperlyConfigured("Set CEREQO_SECRET_KEY before starting the public tunnel mode.")

DEBUG = os.environ.get("CEREQO_DEBUG", "0" if PUBLIC_TUNNEL else "1") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

if PUBLIC_TUNNEL:
    ALLOWED_HOSTS.append(".trycloudflare.com")
    CSRF_TRUSTED_ORIGINS = ["https://*.trycloudflare.com"]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "learning",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cereqo_project.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "learning.context_processors.demo_shell",
            ],
        },
    }
]
WSGI_APPLICATION = "cereqo_project.wsgi.application"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

LANGUAGE_CODE = "uz"
LANGUAGES = [("uz", "O‘zbek"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/learn/"
LOGOUT_REDIRECT_URL = "/"

DEMO_LOGIN_USERNAME = os.environ.get("CEREQO_DEMO_USERNAME", "demo")
DEMO_LOGIN_PASSWORD = os.environ.get("CEREQO_DEMO_PASSWORD", "CereqoDemo2026!")
