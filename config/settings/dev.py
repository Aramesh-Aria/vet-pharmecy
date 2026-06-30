"""Local development settings."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Default to SQLite locally unless DATABASE_URL is set (PLAN §4).
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",  # noqa: F405
    )
}

INTERNAL_IPS = ["127.0.0.1"]
