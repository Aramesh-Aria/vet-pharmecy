# Server-rendered Django templates with HTMX, not an API + SPA

The site is a content-heavy public presence plus a moderate client portal for a
single local practice. We will render all pages with Django templates and add
interactivity with HTMX (plus light Alpine.js), rather than building a Django
REST Framework API behind a React/Vue SPA.

**Why:** One codebase and one mental model, no separate auth-token layer or JS
build pipeline, SEO works out of the box (important for a local business), and
the dynamic needs (booking form, cart, refill request) are well within HTMX's
reach. A SPA would roughly double the surface area for no real benefit at this
scale.

**Consequence:** If a genuinely app-like surface emerges later (e.g. a staff
scheduling calendar), we can add a small JSON endpoint for just that view
without converting the whole site.
