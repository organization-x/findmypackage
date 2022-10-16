from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('FMP_DJANGO_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('FMP_DJANGO_DEBUG') == 'true'

SECRETS = {
    'FEDEX_ID': os.environ.get('FMP_FEDEX_ID'),
    'FEDEX_SECRET': os.environ.get('FMP_FEDEX_SECRET'),
    'USPS_ID': os.environ.get('FMP_USPS_ID'),
    'DHL_SECRET': os.environ.get('FMP_DHL_SECRET'),
    'FMP_MAPS_KEY': os.environ.get('FMP_MAPS_KEY'),
}

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s | %(levelname)-8s | [%(filename)s:%(funcName)s:%(lineno)d] | %(message)s',
            'style': '%',
        },
        'simple': {
            'format': '%(levelname)-8s | %(message)s',
            'style': '%',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': f'{BASE_DIR}/logs/fmp-warning.log',
        },
        'basicfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': f'{BASE_DIR}/logs/fmp-debug.log'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'fmp': {
            'handlers': ['file', 'basicfile', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'package.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR.joinpath('web/templates'))],
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

WSGI_APPLICATION = 'package.wsgi.application'
ASGI_APPLICATION = 'package.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'db.sqlite3',
    }
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

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'main'
LOGOUT_REDIRECT_URL = 'main'

APPEND_SLASH = False

if not os.path.exists(BASE_DIR / 'data'):
    os.makedirs(BASE_DIR / 'data')
    
if not os.path.exists(BASE_DIR / MEDIA_URL):
    os.makedirs(BASE_DIR / MEDIA_URL)

if not os.path.exists(BASE_DIR / 'logs'):
    os.makedirs(BASE_DIR / 'logs')
    open(BASE_DIR / 'logs' / 'fmp-warning.log', 'a').close()
    open(BASE_DIR / 'logs' / 'fmp-debug.log', 'a').close()