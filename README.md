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

**Database** — create a **PostgreSQL** service (16.2 recommended; not PostGIS),
then set `DATABASE_URL=postgres://USER:PASSWORD@<db-service-name>:5432/DBNAME`.
You cannot attach a disk to a database service — RunFlare's managed Postgres
handles its own storage.

**Disk** — add one disk at path **`/app/public`** (Disk Management → Add Disk).
Static and media are served from `/public/` per RunFlare's Django docs:
`STATIC_ROOT=/app/public/static`, `MEDIA_ROOT=/app/public/media`. The disk keeps
**uploaded media** across deploys.

**Start command** — because that disk mounts at **runtime**, run migrate +
collectstatic there (not only at build), so they land on the mounted disk:

```
python manage.py migrate --noinput && \
python manage.py collectstatic --noinput && \
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

**Env vars:** `DJANGO_SETTINGS_MODULE=config.settings.prod`, `DEBUG=False`,
`SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` (defaults include
`vet-pharmecy.runflare.run`). `CSRF_TRUSTED_ORIGINS` defaults to the HTTPS form of
each host. After the first deploy: create a superuser and run
`python manage.py seed_data` from the RunFlare console.

Static uses non-manifest storage (stable filenames like `…/css/app.css`) so
RunFlare serves them by path; WhiteNoise compresses + serves as a fallback. The
source assets live in `static/`; `public/` is generated (gitignored).

## Apps (current)

| App             | Responsibility                                                        |
|-----------------|-----------------------------------------------------------------------|
| `config`        | Split settings (base/dev/prod), URLs, WSGI/ASGI                       |
| `accounts`      | Custom User (phone identity, ADR-0004), OwnerProfile, OTP auth        |
| `core`          | Base templates, Jalali/Persian template filters                      |
| `notifications` | `notify()` + pluggable SMS/email backends; OTP delivery (ADR-0003)   |
| `catalog`       | AnimalCategory + Section taxonomy, Products, browse/filter (ADR-0006) |
| `animals`       | Animal + Herd models, Owner-scoped CRUD                              |
| `pharmacy`      | Cart, Order lifecycle, Prescriptions + Refill Requests               |
| `appointments`  | Appointment request → Staff-confirm lifecycle                        |
| `records`       | Visit Records, Vaccinations + due-date reminder job                  |
| `payments`      | Payment model + backend interface; pay-at-pickup (ADR-0005)          |
| `pages`         | Public home with category tiles                                      |

Public content polish, business-identity/terms pages, and launch hardening are
Phase 4; online payment + the Online Visit are Phase 5 (post-e-Namad).

### Scheduled jobs

`python manage.py send_vaccination_reminders [--days N]` — notify Owners of
vaccinations coming due. Run from cron (e.g. daily) per PLAN §4.
