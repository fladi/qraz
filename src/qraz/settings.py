"""
Django settings for qraz project.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

from docutils.core import publish_parts
from IPy import IP

from django.core.urlresolvers import reverse_lazy as reverse


class IPList(list):

    def __init__(self, addresses):
        super(IPList, self).__init__()
        for address in addresses:
            self.append(IP(address))

    def __contains__(self, address):
        for net in self:
            if address in net:
                return True
        return False

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

SITE_ID = os.environ.get('DJANGO_SITE_ID')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

DEBUG = 'DJANGO_DEBUG' in os.environ
ADMINS = (
    ('Michael Fladischer', 'michael@openservices.at'),
)
EMAIL_HOST = 'localhost'
SERVER_EMAIL = 'django@qraz.at'

if 'DJANGO_INTERNAL_IPS' in os.environ:
    INTERNAL_IPS = IPList(os.environ.get('DJANGO_INTERNAL_IPS').split(','))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
            ),
        },
    },
]

ALLOWED_HOSTS = ['qraz.at', 'www.qraz.at']

INSTALLED_APPS = (
    'qraz.frontend',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oauth2_provider',
    'corsheaders',
    'social.apps.django_app.default',
    'crispy_forms',
    'django_extensions',
    'django_fsm',
    'fsm_admin',
    'guardian',
    'rest_framework',
    'reversion',
    'compressor',
    'djcelery',
    'ws4redis',
)

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django_downloadview.SmartDownloadMiddleware',
)

ROOT_URLCONF = 'qraz.urls'

WSGI_APPLICATION = 'qraz.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.environ.get(
            'DJANGO_DATABASES_DEFAULT_ENGINE',
            'django.db.backends.sqlite3'
        ),
        'NAME': os.environ.get(
            'DJANGO_DATABASES_DEFAULT_NAME',
            os.path.join(BASE_DIR, 'db.sqlite3')
        ),
        'USER': os.environ.get(
            'DJANGO_DATABASES_DEFAULT_USER',
            ''
        ),
        'PASSWORD': os.environ.get(
            'DJANGO_DATABASES_DEFAULT_PASSWORD',
            ''
        ),
        'HOST': os.environ.get(
            'DJANGO_DATABASES_DEFAULT_HOST',
            ''
        ),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'localhost:11211',
        'KEY_PREFIX': __package__,
    }
}
CACHE_MIDDLEWARE_SECONDS = 60
CACHE_MIDDLEWARE_KEY_PREFIX = SITE_ID

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

ANONYMOUS_USER_ID = -1
AUTHENTICATION_BACKENDS = (
    'social.backends.github.GithubOAuth2',
    'guardian.backends.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_URL = reverse('social:begin', args=['github'])
LOGIN_REDIRECT_URL = 'qraz:presentations'

SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_STRATEGY = 'social.strategies.django_strategy.DjangoStrategy'
SOCIAL_AUTH_STORAGE = 'social.apps.django_app.default.models.DjangoStorage'
SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
)

SOCIAL_AUTH_GITHUB_KEY = os.environ.get('DJANGO_SOCIAL_AUTH_GITHUB_KEY')
SOCIAL_AUTH_GITHUB_SECRET = os.environ.get('DJANGO_SOCIAL_AUTH_GITHUB_SECRET')
SOCIAL_AUTH_GITHUB_SCOPE = [
    'user:email',
    'admin:repo_hook',
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'src/static'),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

HOVERCRAFT_ROOT = os.path.join(BASE_DIR, 'hovercraft')

CRISPY_TEMPLATE_PACK = 'bootstrap3'

COMPRESS_ENABLED = not DEBUG
if DEBUG:
    COMPRESS_DEBUG_TOGGLE = 'nocompress'
COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', 'coffee --compile --stdio'),
    ('text/less', 'lessc {infile} {outfile}'),
    ('text/x-sass', 'sass {infile} {outfile}'),
    ('text/x-scss', 'sass --scss {infile} {outfile}'),
    ('text/stylus', 'stylus < {infile} > {outfile}'),
)
COMPRESS_CSS_FILTERS = (
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
)
COMPRESS_JS_FILTERS = (
    'compressor.filters.jsmin.JSMinFilter'
)
COMPRESS_STORAGE = 'compressor.storage.GzipCompressorFileStorage'
COMPRESS_CSS_COMPRESSOR = 'compressor.css.CssCompressor'
COMPRESS_JS_COMPRESSOR = 'compressor.js.JsCompressor'
COMPRESS_OUTPUT_DIR = 'cache'
COMPRESS_PARSER = 'compressor.parser.AutoSelectParser'
COMPRESS_URL = STATIC_URL
COMPRESS_ROOT = STATIC_ROOT

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.DjangoModelPermissions',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ]
}

DOWNLOADVIEW_BACKEND = 'django_downloadview.apache.XSendfileMiddleware'
DOWNLOADVIEW_RULES = [
    {
        'source_url': '/media/apache/',
        'destination_dir': '/apache-optimized-by-middleware/'
    }
]

CORS_ORIGIN_ALLOW_ALL = True

MARKUP_FIELD_TYPES = [
    ('ReST', lambda markup: publish_parts(source=markup, writer_name='html4css1')['body'])
]

BROKER_URL = 'amqp://{username}:{password}@{hostname}/{vhost}'.format(
    hostname=os.environ.get('CELERY_BROKER_HOSTNAME'),
    username=os.environ.get('CELERY_BROKER_USERNAME'),
    password=os.environ.get('CELERY_BROKER_PASSWORD'),
    vhost=os.environ.get('CELERY_BROKER_VHOST')
)
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['pickle']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'qraz.frontend.tasks': {
            'handlers': ['console'],
            'propagate': True,
        },
    },
}
