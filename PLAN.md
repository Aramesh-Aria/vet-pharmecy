# Build Plan — Vet Clinic & Pharmacy Website

This plan is the output of a grilling session, updated after the practice's
feedback (see `conversation.txt`). Settled vocabulary lives in
[CONTEXT.md](./CONTEXT.md); hard-to-reverse decisions are in
[docs/adr/](./docs/adr/). Read those first — this document assumes them.

---

## 1. What we're building

A Farsi/RTL website for **one local veterinary practice that is both a clinic and
a pharmacy/store**, owned by the vet. It is a **mixed practice** serving companion
animals, ornamental birds, horses, and livestock. Two faces:

- **Public site** — marketing pages, organized around the animal categories.
- **Client portal** — logged-in Owners manage their Animals, request
  appointments/consultations, view records, request prescription refills, and buy
  products (paid online, collected at the pharmacy).

It is **not** a multi-tenant SaaS and **not** a full clinical EMR.

## 2. Settled decisions (the spine)

| Area | Decision | Ref |
|------|----------|-----|
| Scope | Single mixed-practice clinic + pharmacy, one Django project | CONTEXT.md |
| Information architecture | **Animal-category first**; home = category tiles; 4 Sections per category | ADR-0006 |
| Customers | Full Owner accounts (client portal) | — |
| Appointments | Owner **requests**, Staff **confirm** (no live calendar in v1) | — |
| Pharmacy/store | Catalog of **Medication + Equipment**, pickup; pay-at-pickup at launch → online later | ADR-0005 |
| Payments | **Online (target)** via an Iranian gateway, but **phased**: blocked until e-Namad, which needs the live site | ADR-0005 |
| Online Visit | Paid, time-boxed **virtual visit** (ویزیت آنلاین), pay-online-at-booking; ships **with the gateway**, not at launch | ADR-0005 |
| Records | **Lightweight**: profile + visit history + vaccinations | — |
| Notifications | **Email + SMS** via one notification layer | ADR-0003 |
| Frontend | Server-rendered Django templates + **HTMX** (+ Alpine) | ADR-0001 |
| Staff UI | **Django admin** (customized) now, custom pages later | — |
| Language | **Farsi-first, RTL, Jalali calendar** | ADR-0002 |
| Login | **Phone + password**, OTP (SMS) for verify/reset; custom User model | ADR-0004 |
| Hosting | **Iranian VPS**: Gunicorn + Nginx + PostgreSQL, Dockerized | — |
| Priority | **Store + Clinic first**; About/Team intro deprioritized | conversation.txt |

## 3. Information architecture (the new backbone)

```
Home  ──►  [Ornamental Birds] [Companion Pets] [Equine] [Ruminants]   (image tiles)
                     │
                     ▼  per-category landing page, four Sections:
        ┌─────────────┬─────────────┬─────────────┬─────────────┐
        │ Online Visit│  Medication │  Equipment  │   Service   │
        │(ویزیت آنلاین)│   (دارو)    │  (تجهیزات)  │  (خدمات)   │
        └─────────────┴─────────────┴─────────────┴─────────────┘
        Service     → in-person, booked via Appointment, pay later
        Online Visit→ paid virtual visit, pay online at booking (post-gateway);
                      global booking, not tied to a registered Animal
        Medication/Equipment → Products → cart → Order → pickup
                      (pay-at-pickup at launch; pay online after the gateway)
```

URL scheme: `/c/<category-slug>/` and `/c/<category-slug>/<section>/...`. Animal
Categories and Sections are data-driven (Staff-editable), not hard-coded.

## 4. Tech stack

- **Python 3.12+, Django 5.x** (a `.venv` already exists).
- **PostgreSQL** in production; SQLite for local dev only.
- **HTMX + Alpine.js**; **Bootstrap 5 (RTL build)** + **Vazirmatn** font; CSS uses
  logical properties for RTL safety.
- **django-jalali / jdatetime** for Jalali dates in the UI.
- **Django i18n** wired from day one, Farsi the only designed locale.
- **Email** via SMTP; **SMS** via an Iran-reachable gateway (Kavenegar / SMS.ir /
  Ghasedak) — never Twilio.
- **Payment** via an Iranian gateway (Zarinpal recommended) behind a `payments`
  abstraction.
- Background work (notifications, vaccination reminders, abandoned-payment
  cleanup): cron-run management commands first; **Celery + Redis** if volume grows.
- **Gunicorn + Nginx + Docker Compose**, deployed to an Iranian VPS.

## 5. Django apps

```
config/          # split settings, urls, wsgi/asgi
accounts/        # custom User (phone identity), Owner profile, auth, OTP
animals/         # Animal (renamed from Pet), Species
catalog/         # AnimalCategory, Section, Product (Medication|Equipment), Service & Online Visit offerings
appointments/    # Appointment Request, Appointment (in-person Service + paid Online Visit)
records/         # Visit Record, Vaccination
pharmacy/        # Cart, Order, OrderItem, Prescription, Refill Request
payments/        # gateway integration, Payment model, start/verify/refund
notifications/   # notify() entry point, email + SMS backends
pages/           # public content: Home (tiles), category pages, About, Contact, Blog
core/            # base templates, RTL/Jalali helpers, mixins
```

## 6. Data model (first cut)

- **User** (`accounts`) — phone (unique identity), password, optional email,
  `role` (owner | staff), phone-verified flag.
- **OwnerProfile** — name, address, notification prefs. 1–1 with User.
- **Animal** (`animals`) — owner FK, animal_category FK, species, name, sex, birth
  date, weight, photo.
- **AnimalCategory** (`catalog`) — name, slug, image (the home tile), order.
- **Section** — enum/choices: online_visit | medication | equipment | service.
- **Product** (`catalog`) — animal_category FK, section (medication|equipment),
  name, description, price, stock, image, `is_prescription_only` (meds only).
- **Service** (`catalog`) — animal_category FK, name, description, approx
  duration, optional price. The in-person offerings booked via Appointment.
- **OnlineVisit slot/offering** — price, duration (e.g. 10 min); NOT linked to an
  Animal. Booked as a paid Appointment with `is_online=True`. Ships post-gateway.
- **AppointmentRequest** / **Appointment** (`appointments`) — owner, optional
  animal (required for Service, omitted for Online Visit), service/online-visit,
  preferred/confirmed time, vet FK, `is_online`, status.
- **VisitRecord**, **Vaccination** (`records`).
- **Cart** / **Order** / **OrderItem** (`pharmacy`) — owner, items, status
  (placed → approved → [paid] → ready-for-pickup → collected / cancelled). The
  `paid` step is settled at pickup until the gateway is live, online thereafter.
- **Prescription**, **RefillRequest** (`pharmacy`).
- **Payment** (`payments`) — links an Order or Online Visit, gateway, amount,
  authority/ref id, status (initiated → paid / failed → refunded), timestamps.
  Inactive until e-Namad + gateway are in place.
- **Article** (`pages`) — blog (later phase).

## 7. Feature surface

**Public (no login)**
- Home with one image tile per Animal Category (the primary entry point).
- Per-category landing pages with the four Sections.
- Browse Products (Medication/Equipment) with filters; browse Service offerings
  and the Online Visit booking.
- Contact + Location and accurate **business-identity pages** (address, phone,
  terms) — these are **required for e-Namad**, so they are pre-launch scope.
  Vet-team bios stay **deprioritized to a later phase** per the practice's request.
- Blog / pet-care articles — later, nice-to-have.

**Owner portal (phone + password)**
- Register, phone OTP verification, login, password reset via OTP.
- Manage Animals (CRUD, photos), each tagged with its Category/Species.
- Request in-person Service appointments (animal + service + preferred times);
  track status. (Paid **Online Visit** booking arrives with the gateway.)
- View visit history and vaccination list with due dates.
- Cart → checkout → **pickup** (pay at pickup at launch; pay online once the
  gateway is live); track Order status.
- Request prescription Refills (Staff approve & price → pickup; pay online later).

**Staff back office (Django admin, customized)**
- Manage Animal Categories, Sections, Products (stock), and Offerings.
- Queue of pending Appointment Requests → confirm / reschedule / decline.
- Manage Appointments, Visit Records, Vaccinations.
- Issue Prescriptions; approve & price Refill/Order requests.
- Process Orders (approve → mark ready → collected); view Payments/refunds.
- Role-based permissions (Veterinarian vs Receptionist).

**Cross-cutting**
- `notify(owner, event, context)` → email + SMS on appointment confirmed/declined,
  order paid/ready, refill ready, vaccination due.
- `payments`: `start_payment(order)` → gateway redirect → verify callback
  (idempotent) → Order/Payment state update.
- Jalali dates and Persian digits throughout.

## 8. Build roadmap (phases)

The hard external dependency shapes everything: **online payment can't exist
until the site is live (→ e-Namad → gateway).** So we ship a complete,
payment-less site first, launch it, then add payments.

**Phase 0 — Foundation**
Scaffold, split settings, PostgreSQL, **custom User model before the first
migration** (ADR-0004), RTL base + Vazirmatn + Bootstrap RTL, i18n + Jalali,
Docker Compose. Stub the `payments` app with a pay-at-pickup backend.

**Phase 1 — Accounts, Animals & Taxonomy**
Phone+password auth + OTP; Owner profile; Animal CRUD; **AnimalCategory / Section
taxonomy**; home page with category tiles; per-category landing pages. Notification
layer skeleton (console backend).

**Phase 2 — Store (high priority, no gateway yet)**
Product catalog (Medication + Equipment) with filters; Cart; Order lifecycle with
**pay-at-pickup**; Prescriptions + Refill Requests with approve-then-pay; Staff
fulfillment in admin. Real email + SMS wired in.

**Phase 3 — Clinic**
In-person **Service** offerings; Appointment Request → Staff-confirm flow; Visit
Records; Vaccinations + due-date reminder job; status notifications.

**Phase 4 — Public content & launch prep**
Home/category pages polish, Contact/Location + **business-identity & terms pages
(needed for e-Namad)**, SEO, accessibility + RTL QA, production hardening.
**→ Deploy to the Iranian VPS. SITE GOES LIVE (payment-less).**

**Milestone — e-Namad (نماد الکترونیک)**
With the live site, apply for and obtain the e-Namad e-trust seal. External/legal
step, not code — but it gates Phase 5.

**Phase 5 — Payments & Online Visit (post-e-Namad)**
Contract an Iranian gateway (Zarinpal/…); add the real `payments` backend; switch
Orders to **pay-online-before-pickup**; build the paid **Online Visit
(ویزیت آنلاین)** — booked slot, online payment at booking, optional electronic
Prescription. Refunds/reconciliation.

**Phase 6 — Later / nice-to-have**
Vet-team bios, Blog/pet-care articles, and anything from §9 as needed.

## 9. Deferred (explicitly out of v1)

- Real-time self-service booking calendar.
- Custom (non-admin) staff dashboard.
- Delivery/shipping of orders (pickup only for now).
- Second language / English locale.
- Full clinical EMR (labs, attachments, SOAP notes).

> **Note:** Online payment is the **target** model but is **phased to after
> launch** (e-Namad → gateway, ADR-0005). The site launches payment-less with
> pay-at-pickup; online payment and the Online Visit arrive in Phase 5.

## 10. Open questions

**Resolved**
- Categories: 4 groups (Ornamental Birds, Companion Pets, Equine, Ruminants) for
  now; more can be added later.
- Service vs Online Visit are distinct. A **Service** is something the clinic
  *does* for the animal (procedure/treatment), in person, pay later. An **Online
  Visit** (ویزیت آنلاین, formerly "Consultation") is a **paid, time-boxed virtual
  visit**, booked in advance, **paid online at booking**, not tied to a registered
  Animal, optionally ending in an electronic Prescription. Ships in Phase 5 with
  the gateway.

**Still open (asked of the practice)**
1. **Livestock registration:** do owners of ruminants (sheep, goat, camel)
   register each animal individually (like cat/dog profiles), or is herd-level
   registration enough? Affects the `Animal` model.
