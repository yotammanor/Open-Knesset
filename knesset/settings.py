# encoding: utf-8
# Django settings for knesset project.
import os
import logging
from datetime import timedelta

# dummy gettext, to get django-admin makemessages to find i18n texts in this file
import sys

gettext = lambda x: x

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'NAME': 'dev.db',
        'ENGINE': 'django.db.backends.sqlite3',
    },
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Jerusalem'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'he'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    os.path.pardir
))

DATA_ROOT = os.path.join(PROJECT_ROOT, 'data', '')

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media', '')

# Absolute path to location of collected static files
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static_root', '')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '1_ovxxkf(c*z_dwv!(-=dezf#%l(po5%#zzi*su-$d*_j*1sr+'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
    # 'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'sslify.middleware.SSLifyMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',  # keep after session
    'django.middleware.csrf.CsrfViewMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'waffle.middleware.WaffleMiddleware',
    # make sure to keep the DebugToolbarMiddleware last
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'social.backends.twitter.TwitterOAuth',
    'social.backends.facebook.FacebookOAuth2',
    'social.backends.google.GoogleOAuth2',
    'social.backends.google.GoogleOAuth',
    'social.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_CREATE_USERS = True
SOCIAL_AUTH_FORCE_RANDOM_USERNAME = False
SOCIAL_AUTH_ASSOCIATE_BY_MAIL = True
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ['username', 'first_name', 'email']

# These keys will work for 127.0.0.1:8000
# and are overriden in the production server.
SOCIAL_AUTH_TWITTER_KEY = 'KFZkQgImAyECXDS6tQTvOw'
SOCIAL_AUTH_TWITTER_SECRET = 's6ir2FMqw4fqXQbX4QCE6Ka1lRjycXxJuG6k8tYc'

ROOT_URLCONF = 'knesset.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'templates'),
)

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),  # Finding current static files
)

LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, 'locale'),
)
INSTALLED_APPS = (
    'django.contrib.auth',  # django apps
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.comments',
    'django.contrib.sitemaps',
    'django.contrib.flatpages',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tastypie_swagger',
    # 'debug_toolbar',
    'tagging',
    'south',
    'planet',
    'pagination',
    'django_extensions',
    'actstream',
    'avatar',

    'annotatetext',
    'mailer',
    'backlinks',
    'backlinks.pingback',
    'backlinks.trackback',
    'django_nose',
    'gunicorn',
    'djangoratings',
    'voting',
    'social.apps.django_app.default',
    'devserver',
    'crispy_forms',
    'storages',
    'corsheaders',
    'sslserver',
    'waffle',
    'import_export',
    'django_slack',
    # 'knesset',
    'auxiliary',  # knesset apps
    'mks',
    'mmm',
    'laws',
    'committees',
    'simple',
    'tagvotes',
    'accounts',
    'links',
    'user',
    'agendas',
    'notify',
    'persons',
    'events',
    'video',
    'okhelptexts',
    'tastypie',
    'polyorg',
    'plenum',
    'tinymce',
    'suggestions',
    'okscraper_django',
    'lobbyists',
    'kikar',
    'ok_tag',
    'dials',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "knesset.context.processor",
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
)

INTERNAL_IPS = ()
# Add the following line to your local_settings.py files to enable django-debug-toolar:
# INTERNAL_IPS = ('127.0.0.1',)

LOCAL_DEV = True

LOGIN_URL = '/users/login/'

SITE_NAME = 'Open-Knesset'

MAX_TAG_LENGTH = 128

AUTH_PROFILE_MODULE = 'user.UserProfile'

LOGIN_REDIRECT_URL = '/'

USER_AGENT = "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)"

formatter = logging.Formatter("%(asctime)s\t%(name)s:%(lineno)d\t%(levelname)s\t%(message)s")
LOG_FILENAME = os.path.join(PROJECT_ROOT, 'open-knesset.log')
oknesset_logger = logging.getLogger("open-knesset")
oknesset_logger.setLevel(logging.DEBUG)  # override this in prod server to logging.ERROR
file_handler = logging.FileHandler(LOG_FILENAME)
file_handler.setLevel(logging.INFO)

file_handler.setFormatter(formatter)
oknesset_logger.addHandler(file_handler)

# Console loggers, Best practice always log to stdout and stderr and let third party environment to deal with logging
# See 12 factor app http://12factor.net/logs
# Todo refactor this to support stderr and out and more dynamic config supporting sentry etc
root_logger = logging.getLogger('')  # root logger
root_logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(stream=sys.stdout)

stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(logging.INFO)

stderr_handler = logging.StreamHandler(stream=sys.stderr)

stderr_handler.setFormatter(formatter)
stderr_handler.setLevel(logging.ERROR)

root_logger.addHandler(stderr_handler)
root_logger.addHandler(stdout_handler)

request_logger = logging.getLogger('requests')
request_logger.setLevel(logging.ERROR)
request_logger.addHandler(stderr_handler)

opbeat_logger = logging.getLogger('opbeat.errors')
request_logger.setLevel(logging.ERROR)
request_logger.addHandler(stderr_handler)
request_logger.addHandler(stderr_handler)

GOOGLE_CUSTOM_SEARCH = "007833092092208924626:1itz_l8x4a4"
GOOGLE_MAPS_API_KEYS = {'dev': 'ABQIAAAAWCfW8hHVwzZc12qTG0qLEhQCULP4XOMyhPd8d_NrQQEO8sT8XBQdS2fOURLgU1OkrUWJE1ji1lJ-3w',
                        'prod': 'ABQIAAAAWCfW8hHVwzZc12qTG0qLEhR8lgcBs8YFes75W3FA_wpyzLVCpRTF-eaJoRuCHAJ2qzVu-Arahwp8QA'}
GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_API_KEYS['dev']  # override this in prod server

# you need to generate a token and put it in local_settings.py
# to generate a token run: bin/django update_videos --get-youtube-token
YOUTUBE_AUTHSUB_TOKEN = ''

# you need to get a developer key and put it in local_settings.py
# to get a developer key goto: http://code.google.com/apis/youtube/dashboard
YOUTUBE_DEVELOPER_KEY = ''

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

LONG_CACHE_TIME = 18000  # 5 hours

ANNOTATETEXT_FLAGS = (
    gettext('Statement'),
    gettext('Funny :-)'),
    gettext('False fact'),
    gettext('Source?'),
    gettext('Found source'),
    gettext('Cross reference'),
    gettext('Important'),
    gettext('Formatting/Error!'),
    gettext('Comment'),
)

AUTO_GENERATE_AVATAR_SIZES = (75, 48)
AVATAR_GRAVATAR_BASE_URL = 'https://www.gravatar.com/avatar/'

NOSE_ARGS = ['--with-xunit']

SERIALIZATION_MODULES = {
    'oknesset': 'auxiliary.serializers'
}

API_LIMIT_PER_PAGE = 1000

SOUTH_TESTS_MIGRATE = False

SOUTH_MIGRATION_MODULES = {

    'waffle': 'waffle.south_migrations',
}

TINYMCE_DEFAULT_CONFIG = {
    'mode': "textareas",
    'theme': "advanced",
    'plugins': "paste",
    'theme_advanced_buttons1': ("bold,italic,underline,|,undo,redo,|,"
                                "link,unlink,|,bullist,numlist,|"
                                ",cut,copy,paste,pastetext,|,cleanup"),
    'theme_advanced_buttons2': "",
    'theme_advanced_buttons3': "",
    'theme_advanced_toolbar_align': "center",

}

DEVSERVER_DEFAULT_ADDR = '127.0.0.1'
DEVSERVER_DEFAULT_PORT = 8000

# This is for socialauth is it can't serilaize correctly datetime.datetime. A
# JSON serialzer is preferred and changed to be the default in 1.6, but we'll
# have to keep it for now. For more info, see:
# https://docs.djangoproject.com/en/1.5/topics/http/sessions/#session-serialization
#
# TODO: Look into switching to django-allauth instead and using the session
# serializer.
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

TASTYPIE_SWAGGER_API_MODULE = 'apis.resources.v2_api'

# By default auto-SSL disabled, on production machines local_settings overrides
# to False
SSLIFY_DISABLE = True

# in production you might want to limit it in local_settings
CORS_ORIGIN_ALLOW_ALL = True

JWT_EXPIRATION_DELTA = timedelta(hours=48)
JWT_ALGORITHM = 'HS256'

LOGIN_REDIRECT_TARGETS = {
    'opensubs': {
        'parent_location_href': 'http://localhost:9000/',
        'redirect_to_url': 'http://localhost:9000/#/login/',
        'fb_secret': ''
    }
}

KIKAR_BASE_URL = 'http://www.kikar.org'

# if you add a local_settings.py file, it will override settings here
# but please, don't commit it to git.
DEBUG_TOOLBAR_PATCH_SETTINGS = False

TEST_RUNNER = 'knesset.common_test_runner.KnessetTestRunner'

DEVSERVER_MODULES = (
    # 'devserver.modules.sql.SQLRealTimeModule',
    'devserver.modules.sql.SQLSummaryModule',
    'devserver.modules.profile.ProfileSummaryModule',
    # 'devserver.modules.profile.MemoryUseModule'
)

try:
    from local_settings import *
except ImportError:
    pass
