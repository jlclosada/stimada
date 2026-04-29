import dj_database_url
from decouple import config

from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES = {
    "default": dj_database_url.config(default=config("DATABASE_URL"))
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
