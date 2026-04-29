import dj_database_url
from decouple import config

from .base import *  # noqa: F401, F403

DEBUG = True

DATABASES = {
    "default": dj_database_url.config(
        default=config(
            "DATABASE_URL",
            default="postgres://stimada:stimada@db:5432/stimada",
        )
    )
}

# Enable Django debug toolbar in local if installed
INTERNAL_IPS = ["127.0.0.1"]
