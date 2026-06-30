# Frontend Design Brief — Vet Clinic & Pharmacy

This document is the **handover brief for the visual/UX design phase** (to be done
with claude design + the ui-ux-pro-max skill, guided by reference screenshots from
other veterinary-clinic sites). The **backend is already built** (Phases 0–3); this
brief tells the designer *what* exists, *what screens must be designed*, and the
*hard constraints* — and deliberately leaves all visual/branding decisions open.

> Deeper background lives in [`PLAN.md`](../PLAN.md), [`CONTEXT.md`](../CONTEXT.md),
> and [`docs/adr/`](./adr/). Read this brief first; those for detail.

---

## 1. What this is (in one paragraph)

A **Farsi / right-to-left website for a single local veterinary practice that is
both a clinic and a pharmacy**, owned by the vet. It is a **mixed practice** —
it serves **companion pets, ornamental birds, horses, and livestock**, not only
pets. There are two faces: a **public site** (marketing + catalog, organized by
animal category) and a **logged-in client portal** (owners manage their animals,
book appointments, buy products for pickup, request prescription refills). It is
**not** a multi-clinic SaaS and **not** a full medical-records system.

**Priority from the practice owner:** the **Store and Clinic come first**;
about-us/team bios and blog are deprioritized.

---

## 2. Non-negotiable constraints (the design must honor these)

| Constraint | Detail |
|---|---|
| **Language** | **Farsi only**, professionally written. No English UI. |
| **Direction** | **RTL** (`dir="rtl"`, `lang="fa"`). Layout, icons, arrows, carousels all flow right-to-left. Use logical CSS (`margin-inline-start`, not `margin-left`). |
| **Font** | **Vazirmatn** (Persian web font), bundled locally — do **not** rely on a CDN (Iran reachability). |
| **Calendar** | Dates shown to users are **Jalali (Shamsi)**, e.g. ۱۴۰۳/۰۴/۰۹ — never Gregorian. |
| **Digits** | **Persian digits** everywhere (۰۱۲۳۴۵۶۷۸۹), including prices, counts, phone numbers. |
| **Money** | Prices are in **Rial**, shown with thousands separators + Persian digits (e.g. «۵٬۰۰۰٬۰۰۰ ریال»). |
| **Tech stack** | **Server-rendered Django templates + HTMX + light Alpine.js + Bootstrap 5 (RTL build)**. This is **not** a React/SPA. Designs must be implementable as HTML/CSS templates with progressive enhancement (HTMX for cart updates, form submits, filters). No client-side router, no heavy JS framework. |
| **Assets** | Self-hosted (fonts, CSS, JS). No external CDNs. |
| **Performance/SEO** | Public pages must be crawlable and light (local-business SEO matters). |
| **Trust / legal** | Accurate **business-identity pages** (contact, address, hours, terms) are **required for e-Namad** (the Iranian e-trust seal) and must exist before launch. |

**Already available in templates** (reuse, don't reinvent): a base layout
(`templates/base.html`) with blocks `title`, `extra_head`, `content`, `extra_body`;
and Persian template filters `fa_digits`, `jalali`, `toman` (in `core/templatetags/persian.py`).
The current templates are **unstyled placeholders** — the design replaces their look,
not their structure/URLs.

---

## 3. Information architecture (the backbone — ADR-0006)

Navigation is **animal-category first**, then **section** within a category.

```
HOME ──► 4 Animal-Category tiles (image tiles):
         • پرندگان زینتی (Ornamental Birds)
         • حیوانات خانگی  (Companion Pets — cat, dog)
         • اسب           (Equine — horse)
         • نشخوارکنندگان  (Ruminants — sheep, goat, camel)
              │
              ▼  each category landing page shows FOUR sections:
   ┌──────────────┬───────────┬───────────┬───────────┐
   │ ویزیت آنلاین  │   دارو    │  تجهیزات  │   خدمات   │
   │ Online Visit │ Medication│ Equipment │  Service  │
   └──────────────┴───────────┴───────────┴───────────┘
     Medication / Equipment → product catalog → cart → order → pickup
     Service                → list of services → request an appointment
     Online Visit           → paid virtual visit (NOT live yet — Phase 5)
```

- Categories are **data-driven** (staff can add/edit/reorder them), so the home
  grid must handle a **variable number of tiles** (today 4, could be more/fewer).
- URL scheme already built: `/c/<category-slug>/` and
  `/c/<category-slug>/<section>/` and `/c/<category-slug>/<section>/<product-slug>/`.

---

## 4. The domain model (entities behind the screens)

So the designer knows what data each page renders. (Canonical glossary in CONTEXT.md.)

- **Practice** — the single business. Global identity: name, logo, address, phone, hours.
- **Owner** — a customer account, identified by **mobile phone** (login = phone + password; SMS one-time codes for verify/reset). Has a profile (name, address, SMS/email notification prefs).
- **Animal** — an individual pet/horse owned by an Owner: name, **Animal Category**, **Species** (cat/dog/horse…), sex, birth date, weight, photo. Has visit history + vaccinations.
- **Herd** — a livestock group record (Ruminants) instead of one row per head: species, head-count, farm location. (Farmers don't register 200 individual animals.)
- **Animal Category** — top-level grouping with a name, slug, and **tile image**. Drives the whole IA.
- **Section** — fixed set of four: Online Visit, Medication, Equipment, Service.
- **Product** — a pharmacy item: **Medication** or **Equipment**. Has category, name, description, **price (Rial)**, **stock**, image, and a **prescription-only** flag (meds). Browsable by anyone.
- **Service** — an in-person clinical offering (exam, vaccination, dental, surgery…): name, description, approx duration, optional price. Booked via an Appointment.
- **Cart → Order** — Owner's purchase of Products, **collected at the pharmacy**. Order states: ثبت‌شده → تأییدشده → آمادهٔ تحویل → تحویل‌شده / لغوشده. **Payment is at pickup** for now (no online gateway yet).
- **Prescription** — a vet-issued authorization (for a specific Animal + a prescription-only Medication). Created by staff, **shown to the owner**.
- **Refill Request** — owner asks to re-dispense an existing Prescription; staff **approve & price** it; then it's payable at pickup.
- **Appointment** — owner **requests** a Service visit (animal + service + preferred date); **staff confirm** a time. States: درخواست‌شده → تأییدشده → انجام‌شده / لغوشده / عدم‌مراجعه. No live self-service calendar in v1.
- **Visit Record** — clinical note attached to a completed visit (date, service, vet notes). Forms the animal's history.
- **Vaccination** — vaccine + date given + optional next-due date (drives SMS reminders).
- **Payment** — online payment record. **Inactive at launch** (arrives Phase 5 with the gateway + e-Namad).
- **Notifications** — owners get **SMS + email** (appointment confirmed/declined, order ready, refill ready, vaccination due).

---

## 5. Screen inventory (what must be designed)

**Audience key:** 🌐 public · 🔒 owner (logged-in) · 🛠️ staff (Django admin — *not* part
of this public-frontend design, listed for context only).

### A. Public marketing + catalog 🌐
| Screen | Route | Key elements |
|---|---|---|
| **Home** | `/` | Hero/intro; **grid of Animal-Category tiles** (image + name); entry point to everything; trust signals; header w/ login + cart. |
| **Category landing** | `/c/<slug>/` | Category header; the **four section cards** (Online Visit / Medication / Equipment / Service). |
| **Product list** (Medication or Equipment) | `/c/<slug>/medication/`, `/c/<slug>/equipment/` | Product grid/cards (image, name, price, stock/“ناموجود”, “فقط با نسخه” badge); **filters**: search box + “only in stock”. HTMX-friendly filtering. |
| **Product detail** | `/c/<slug>/<section>/<product-slug>/` | Image, description, price; **add-to-cart** w/ quantity (or “only via prescription” notice if Rx-only); out-of-stock state. |
| **Service list** | `/c/<slug>/service/` | List of services (name, duration, optional price, description) each with a **“request appointment”** call-to-action. |
| **Online Visit (placeholder)** | `/c/<slug>/online_visit/` | “Coming after online payment is enabled” state. Design a graceful **coming-soon** treatment. |
| **Contact / Location** | (to build, Phase 4) | Address, map, phone, hours — **needed for e-Namad**. |
| **Terms / business identity** | (to build, Phase 4) | Legal/terms, business info — **needed for e-Namad**. |
| **About / Team, Blog** | later | **Deprioritized** by the practice. Low priority; design last or stub. |

### B. Auth 🌐→🔒
| Screen | Route | Notes |
|---|---|---|
| **Login** | `/accounts/login/` | Phone + password. Links to register + reset. |
| **Register** | `/accounts/register/` | Phone + name + password → sends SMS code. |
| **Verify phone (OTP)** | `/accounts/register/verify/` | Enter 6-digit code; resend option. |
| **Reset request** | `/accounts/reset/` | Enter phone → sends code. |
| **Reset confirm** | `/accounts/reset/confirm/` | Code + new password. |

*(OTP entry deserves nice UX: large numeric input, Persian digits, countdown/resend.)*

### C. Owner portal 🔒
| Screen | Route | Key elements |
|---|---|---|
| **My Animals** | `/animals/` | List of Animals **and** Herds; add buttons. |
| **Animal add/edit** | `/animals/new/`, `/animals/<id>/edit/` | Form incl. photo upload, category/species, birth date (Jalali picker), weight. |
| **Animal detail** | `/animals/<id>/` | Profile + **visit history** + **vaccination list (with due dates)**. |
| **Herd add/edit/detail** | `/animals/herds/...` | Lighter form: species, head-count, farm location. |
| **Cart** | `/shop/cart/` | Line items, qty update, remove, total; **checkout** CTA. Today “pay at pickup”; design must also accommodate a **“pay online”** variant (see below). |
| **Order list / detail** | `/shop/orders/`, `/shop/orders/<id>/` | Status timeline (placed→approved→ready→collected); items; total; payment state (“pay at pickup” *or* “paid online”). |
| **Payment result** (online) | `/payments/callback/` | **Success / failure** result page after returning from the gateway: ref id on success, retry/return on failure. Design both states. |
| **Prescriptions** | `/shop/prescriptions/` | Owner's prescriptions; each with a **“request refill”** action. |
| **Refill list / detail** | `/shop/refills/`, `/shop/refills/<id>/` | Status + price (once staff price it) + “pay at pickup”. |
| **Appointments list** | `/clinic/` | Owner's appointments + status; “new request” button. |
| **Appointment request** | `/clinic/request/` | Pick animal + service + **preferred Jalali date** + note. |
| **Appointment detail** | `/clinic/<id>/` | Status, confirmed time (if any), vet, cancel button when allowed. |

### D. Staff back office 🛠️
Runs on **Django admin** (customized), **not** part of this public design. Mention
only so the designer knows staff workflows live elsewhere.

---

## 6. Cross-cutting UI patterns to design

- **Header / nav:** logo, category menu, and (when logged in) links to My Animals,
  Appointments, Orders, Prescriptions, **Cart (with item count)**, account/logout.
  Logged-out: Login / Register.
- **Status badges:** orders, refills, appointments all have Farsi status states —
  design a consistent badge/timeline system (e.g. requested / confirmed / ready / done / cancelled).
- **Empty states:** “no animals yet”, “cart empty”, “no prescriptions”, etc.
- **Forms:** RTL labels above fields; inline Farsi validation errors; Jalali date
  inputs; numeric inputs for phone/OTP/quantity.
- **Flash messages:** success/error banners (Django messages framework).
- **“Pay at pickup” messaging:** recurring, reassuring note wherever money appears
  (no online payment yet). Design should make this clear, not look broken.
- **Prescription-only products:** clearly badged; cannot be added to cart — route
  the user to the prescription/refill flow instead.
- **Mobile-first:** most owners are on phones. RTL responsive layouts are essential.

---

## 7. Scope of this design pass (what to design now vs. defer)

Refined after a scope discussion. The rule: **design now if it avoids a second
design pass and the requirements are known; defer if it's blocked on an external
dependency or an undecided business rule.**

**Design now (even though some ship later):**
- **Online-payment checkout + result screens.** The backend flow is already built
  behind a feature flag (`PAYMENTS_ONLINE_ENABLED`, off until Phase 5 / e-Namad).
  Design the "pay online" checkout step and the payment **success / failure**
  result pages now so there's no rework later. (See the new rows in §5.)
- **Online Visit** entry/booking *as a coming-soon state* — it's intrinsically
  pay-online, so it activates with the gateway. Design a graceful placeholder.

**Defer — blocked on business decisions, don't design yet:**
- **Order delivery / shipping.** Pickup-only at launch. The practice's intended
  model is captured in `PLAN.md` §9 (Post + Tipax everywhere; Snapp! Box
  intra-city only), but fees / COD / couriers aren't finalized — designing the
  address+method+tracking screens now would be against unknowns.

**Defer — handled elsewhere / later:**
- **Custom staff dashboard** — staff use the **Django admin**, now enhanced with an
  operational dashboard (pending appointments, orders, refills, due vaccinations).
  A bespoke staff UI comes later, informed by real usage. **Not part of this
  public-frontend design.**
- **Live self-service booking calendar** — v1 is request-then-staff-confirm.

**Out of scope entirely:**
- **English / second language** — Farsi only.
- **Full medical-records UI** (labs, attachments, SOAP notes).

---

## 8. Tone & brand cues (starting point — refine with references)

- **Trustworthy, clean, local, warm-but-professional.** It's a real neighborhood
  clinic + pharmacy, not a flashy startup.
- **Mixed practice:** imagery and category art should represent **pets, birds,
  horses, and livestock** — not only cats/dogs.
- Persian typographic comfort: generous line-height, proper Farsi punctuation,
  readable numerals.
- The owner will provide **reference screenshots** from other vet sites for visual
  direction; treat those as the look-and-feel north star, adapted to RTL/Farsi and
  to this site's category-first IA.

---

## 9. Suggested questions the designer should resolve with the owner

(Hand these to claude design as starting clarifications — it will likely ask more.)

1. Logo, brand colors, and any existing visual identity?
2. Real category tile images (or commissioned/stock art) per animal category?
3. Home page beyond tiles — hero message, featured products, promotions, testimonials?
4. How prominent should the **pharmacy/store** be vs. the **clinic** on the home page (owner said store + clinic are the priority)?
5. Photography style: real clinic photos vs. illustrations?
6. Contact page: embedded map provider that works in Iran (e.g. Neshan) and exact address/hours?
7. Any content for Terms/business-identity pages (needed for e-Namad)?
8. Desired density: catalog as cards vs. compact list?

---

## 9b. Which design skill & how to drive it

Primary: the **Anthropic `frontend-design`** skill — it's framework-agnostic and
outputs semantic HTML/CSS that maps cleanly into this project's **Bootstrap-RTL +
Django-templates + HTMX** stack, and it won't fight the Farsi/RTL + self-hosted-
Vazirmatn constraints. Use **`ui-ux-pro-max`** only as a *secondary reference*
(its UX/accessibility checklists and pattern ideas) — **ignore its Tailwind/React
code output and Google-Fonts CDN defaults**, which conflict with §2.

Lead the design session with **§2 constraints + this brief first**, then the
owner's reference screenshots — otherwise either skill defaults to a Tailwind /
Google-Fonts / LTR baseline that has to be undone.

## 10. Handover checklist

- [ ] Designer reads this brief + `CONTEXT.md` (vocabulary) + ADR-0006 (IA).
- [ ] Owner provides reference screenshots + brand assets + category images.
- [ ] Design covers **§5 screen inventory**, honoring **§2 constraints**.
- [ ] Output must be implementable in **Django templates + Bootstrap RTL + HTMX**
      (reuse `base.html` blocks and the `fa_digits`/`jalali`/`toman` filters).
- [ ] RTL + Jalali + Persian digits verified on every screen.
- [ ] Business-identity/contact/terms designed (e-Namad prerequisite).
