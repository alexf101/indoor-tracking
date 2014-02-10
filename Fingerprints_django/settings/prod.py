# noinspection PyUnresolvedReferences
from Fingerprints_django.settings.common import *

environment = "prod"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # 'doj.backends.zxjdbc.mysql',
        'NAME': 'Djangoprints',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'Django',
        'PASSWORD': 'dj12345678',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

TIME_ZONE = 'Australia/Melbourne'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/home/ubuntu/fingerprints_server/static/'

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "/home/ubuntu/fingerprints_server/Django.log",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'logfile'],
            'level': 'WARNING',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'FingerprintsREST': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    }
}
