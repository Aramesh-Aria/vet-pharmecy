"""Local development settings."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0","vet-pharmecy.runflare.run"]

# Default to SQLite locally unless DATABASE_URL is set (PLAN §4).
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'database/db.sqlite3'}",  # noqa: F405
    )

}

INTERNAL_IPS = ["127.0.0.1"]

# Plain static storage in dev — no manifest/compression (that's for prod, and it
# otherwise errors on admin assets before collectstatic runs).
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}
