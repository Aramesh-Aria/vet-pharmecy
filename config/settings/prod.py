"""Production settings — RunFlare (Gunicorn + PostgreSQL; static/media on a
/app/public disk). See README for the deploy steps."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# Must be provided in production.
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# PostgreSQL is required in production; no SQLite fallback.
DATABASES = {"default": env.db("DATABASE_URL")}

# Behind Nginx terminating TLS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=2592000)  # 30 days
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
# Trust the site's own HTTPS origin(s) for POST/CSRF (Django 4+). Defaults to the
# non-local ALLOWED_HOSTS (e.g. https://vet-pharmecy.runflare.run) so forms work
# out of the box; override with CSRF_TRUSTED_ORIGINS in the environment.
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        f"https://{h}"
        for h in ALLOWED_HOSTS
        if h not in ("localhost", "127.0.0.1", "0.0.0.0")
    ],
)

# Transactional email over SMTP in production (Phase 2 wires the provider).
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
