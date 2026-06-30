# Vet Clinic & Pharmacy

Farsi/RTL website for a single mixed-practice veterinary clinic and pharmacy.
See [PLAN.md](./PLAN.md), [CONTEXT.md](./CONTEXT.md), and [docs/adr/](./docs/adr/)
for the design. This repo is being built backend-first; the full frontend is
designed later with claude-design.

## Stack

Django 5.2 · PostgreSQL (prod) / SQLite (dev) · server-rendered templates + HTMX
(later) · Jalali calendar · Gunicorn + WhiteNoise. Deployed on **RunFlare**
(Iranian PaaS) straight from the git repo — no Docker.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate   # already present
pip install -r requirements-dev.txt
cp .env.example .env                                 # adjust as needed
python manage.py migrate
python manage.py createsuperuser                     # prompts for phone + password
python manage.py runserver
```

Dev uses SQLite by default and `config.settings.dev`. Tests: `pytest`.

## Production (RunFlare)

Deployed on RunFlare directly from the git repo (no Docker, no Procfile).
Configure in the RunFlare dashboard:

- **Env vars:** `DJANGO_SETTINGS_MODULE=config.settings.prod`, `SECRET_KEY`,
  `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `DATABASE_URL` (from the attached
  PostgreSQL service).
- **Start command:** `gunicorn config.wsgi:application`
- **Release/build steps:** `python manage.py migrate` and
  `python manage.py collectstatic --noinput`.

WhiteNoise serves static files from the app, so no separate web server is needed.

## Apps (current)

| App             | Responsibility                                                        |
|-----------------|-----------------------------------------------------------------------|
| `config`        | Split settings (base/dev/prod), URLs, WSGI/ASGI                       |
| `accounts`      | Custom User (phone identity, ADR-0004), OwnerProfile, OTP auth        |
| `core`          | Base templates, Jalali/Persian template filters                      |
| `notifications` | `notify()` + pluggable SMS/email backends; OTP delivery (ADR-0003)   |
| `catalog`       | AnimalCategory + Section taxonomy, category landing pages (ADR-0006)  |
| `animals`       | Animal + Herd models, Owner-scoped CRUD                              |
| `payments`      | Payment model + backend interface; pay-at-pickup (ADR-0005)          |
| `pages`         | Public home with category tiles                                      |

Apps for appointments, records, and pharmacy arrive in Phases 2–3 (see PLAN.md §8).
