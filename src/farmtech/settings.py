"""
Django settings for farmtech project.
"""

# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

# Django settings for the GeoNode project.
import os
import ast

try:
    from urllib.parse import urlparse, urlunparse
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request
    from urlparse import urlparse, urlunparse
# Load more settings from a file called local_settings.py if it exists
try:
    from farmtech.local_settings import *
#    from geonode.local_settings import *
except ImportError:
    from geonode.settings import *

#
# General Django development settings
#
PROJECT_NAME = "farmtech"

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith("/"):
    SITEURL = "{}/".format(SITEURL)

SITENAME = os.getenv("SITENAME", "farmtech")

# Defines the directory that contains the settings file as the LOCAL_ROOT
# It is used for relative settings elsewhere.
LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))

WSGI_APPLICATION = "{}.wsgi.application".format(PROJECT_NAME)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "en")

if PROJECT_NAME not in INSTALLED_APPS:
    INSTALLED_APPS += ("farmtech.apps.FarmtechConfig",)

# Swagger/OpenAPI configuration
INSTALLED_APPS += ("drf_yasg",)

# Location of url mappings
ROOT_URLCONF = os.getenv("ROOT_URLCONF", "{}.urls".format(PROJECT_NAME))

# Additional directories which hold static files
# - Give priority to local geonode-project ones
STATICFILES_DIRS = [
    os.path.join(LOCAL_ROOT, "static"),
] + STATICFILES_DIRS

# Location of locale files
LOCALE_PATHS = (os.path.join(LOCAL_ROOT, "locale"),) + LOCALE_PATHS

TEMPLATES[0]["DIRS"].insert(0, os.path.join(LOCAL_ROOT, "templates"))
loaders = TEMPLATES[0]["OPTIONS"].get("loaders") or [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
# loaders.insert(0, 'apptemplates.Loader')
TEMPLATES[0]["OPTIONS"]["loaders"] = loaders
TEMPLATES[0].pop("APP_DIRS", None)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d "
            "%(thread)d %(message)s"
        },
        "simple": {
            "format": "%(message)s",
        },
    },
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "geonode": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "geoserver-restconfig.catalog": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "owslib": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "pycsw": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "celery": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "mapstore2_adapter.plugins.serializers": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "geonode_logstash.logstash": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "farmtech": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

CENTRALIZED_DASHBOARD_ENABLED = ast.literal_eval(
    os.getenv("CENTRALIZED_DASHBOARD_ENABLED", "False")
)
if (
    CENTRALIZED_DASHBOARD_ENABLED
    and USER_ANALYTICS_ENABLED
    and "geonode_logstash" not in INSTALLED_APPS
):
    INSTALLED_APPS += ("geonode_logstash",)

    CELERY_BEAT_SCHEDULE["dispatch_metrics"] = {
        "task": "geonode_logstash.tasks.dispatch_metrics",
        "schedule": 3600.0,
    }

LDAP_ENABLED = ast.literal_eval(os.getenv("LDAP_ENABLED", "False"))
if LDAP_ENABLED and "geonode_ldap" not in INSTALLED_APPS:
    INSTALLED_APPS += ("geonode_ldap",)

# Add your specific LDAP configuration after this comment:
# https://docs.geonode.org/en/master/advanced/contrib/#configuration

if (
    "geonode.base.context_processors.resource_urls"
    in TEMPLATES[0]["OPTIONS"]["context_processors"]
):
    pass

# Add FarmTech context processor
TEMPLATES[0]["OPTIONS"]["context_processors"].append(
    "farmtech.context_processors.farmtech_user"
)

INSTALLED_APPS += ("rest_framework.authtoken",)


DATABASE_ROUTERS += [
    "farmtech.db_router.CustomRouter",
]

# Email configuration for Aruba
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtps.aruba.it")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))
EMAIL_USE_SSL = ast.literal_eval(os.getenv("EMAIL_USE_SSL", "True"))
EMAIL_USE_TLS = ast.literal_eval(os.getenv("EMAIL_USE_TLS", "False"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# copernicus settings
COPERNICUS_CLIENT_ID = os.environ.get("COPERNICUS_CLIENT_ID")
COPERNICUS_CLIENT_SECRET = os.environ.get("COPERNICUS_CLIENT_SECRET")
COPERNICUS_API_URL = os.environ.get("COPERNICUS_API_URL")
COPERNICUS_AUTH_URL = os.environ.get("COPERNICUS_AUTH_URL")

# Django REST Framework Configuration
REST_FRAMEWORK.update(
    {
        "DEFAULT_THROTTLE_CLASSES": [
            "rest_framework.throttling.AnonRateThrottle",
            "rest_framework.throttling.UserRateThrottle",
        ],
        "DEFAULT_THROTTLE_RATES": {
            "anon": "200/hour",  # Global rate limit for anonymous users
            "user": "1000/hour",  # Global rate limit for authenticated users
            # Spacific rate limits are set in the throttling classes
        },
    }
)

SESSION_COOKIE_AGE = 43200
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Override cache backend to use the correct pymemcache backend
CACHES["default"] = {
    "BACKEND": "django.core.cache.backends.memcached.PyLibMCCache",
    "LOCATION": os.getenv("MEMCACHED_LOCATION", "memcached:11211"),
}

# Configure django-select2 to use the default cache
SELECT2_CACHE_BACKEND = "default"

PROXY_ALLOWED_HOSTS = ()
