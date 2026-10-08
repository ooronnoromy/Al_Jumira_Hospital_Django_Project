import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

PRODUCTION = os.getenv('DJANGO_ENV') == 'production' or bool(os.getenv('RAILWAY_ENVIRONMENT_ID'))
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'development-only-change-this')
DEBUG = os.getenv('DJANGO_DEBUG', '0' if PRODUCTION else '1') == '1'
if PRODUCTION and (DEBUG or len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5):
    raise ImproperlyConfigured('Production requires DJANGO_DEBUG=0 and a strong DJANGO_SECRET_KEY of at least 50 characters.')
ALLOWED_HOSTS = [x.strip() for x in os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if x.strip()]
railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '').strip()
if railway_domain:
    ALLOWED_HOSTS.append(railway_domain)
if PRODUCTION:
    ALLOWED_HOSTS.append('healthcheck.railway.app')
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if x.strip()]
if railway_domain:
    CSRF_TRUSTED_ORIGINS.append('https://' + railway_domain)

INSTALLED_APPS = [

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'hospital',

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
ROOT_URLCONF = 'pulse_hms.urls'
WSGI_APPLICATION = 'pulse_hms.wsgi.application'
ASGI_APPLICATION = 'pulse_hms.asgi.application'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates"
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },

    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [
            BASE_DIR / "templates"
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "hospital.jinja2.environment",
        },
    },
]

database_url = os.getenv('DATABASE_URL', '').strip()
if database_url:
    DATABASES = {'default': dj_database_url.parse(database_url, conn_max_age=60, conn_health_checks=True)}
    if PRODUCTION and DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
        raise ImproperlyConfigured('DATABASE_URL must point to PostgreSQL in production.')
    DATABASES['default']['ATOMIC_REQUESTS'] = True
elif os.getenv('USE_SQLITE', '0') == '1':
    if PRODUCTION:
        raise ImproperlyConfigured('Use PostgreSQL in production; set DATABASE_URL.')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.getenv('SQLITE_NAME', 'dev.sqlite3'),
            'ATOMIC_REQUESTS': True,
        }
    }
else:
    if PRODUCTION and not all(os.getenv(key) for key in ('POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST')):
        raise ImproperlyConfigured('Set DATABASE_URL or all POSTGRES connection variables in production.')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'hospital_db'),
            'USER': os.getenv('POSTGRES_USER', 'hospital_user'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'change-me'),
            'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 60,
            'ATOMIC_REQUESTS': True,
        }
    }

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
WHITENOISE_USE_FINDERS = DEBUG
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
ADVERTISEMENT_ROOT = Path(os.getenv('ADVERTISEMENT_ROOT', str(BASE_DIR / 'assets' / 'advertisements')))

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'
if PRODUCTION:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r'^healthz/$']
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    X_FRAME_OPTIONS = 'DENY'
CSRF_FAILURE_VIEW = 'hospital.csrf.csrf_failure'

DATA_UPLOAD_MAX_MEMORY_SIZE = 160 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
APPEND_SLASH = False
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
