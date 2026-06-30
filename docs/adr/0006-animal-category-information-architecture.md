# Animal-category-first information architecture

The site is organized **by Animal Category first**, then by Section within each
category. This came directly from the practice's domain feedback.

**Structure:**

- Top-level **Animal Categories**: Ornamental Birds, Companion Pets (cat, dog),
  Equine (horse), Ruminants (sheep, goat, camel). The set is data-driven
  (editable by Staff), not hard-coded.
- The **home page** presents one image tile per Animal Category. Clicking a tile
  enters that category's landing page.
- Each category landing page exposes four **Sections**: Online Visit
  (ویزیت آنلاین), Medication (دارو), Equipment (تجهیزات), Service (خدمات).
- Medication & Equipment resolve to **Products** (catalog + cart + Order);
  Service resolves to an in-person **Appointment**; **Online Visit** is a paid
  virtual booking surfaced here but not bound to the category or a registered
  Animal (see ADR-0005, CONTEXT.md).

**Why record it:** this is the backbone of navigation, the catalog data model,
and the URL scheme (`/category/<slug>/<section>/...`). A future reader would
otherwise assume a flat product catalog. Every Product and every offering must
carry both an Animal Category and a Section, so the taxonomy is foundational, not
cosmetic.

**Implication:** the practice is a **mixed practice** (companion + avian + equine
+ livestock). "Pet" is therefore one category, not the umbrella term — the
umbrella term is "Animal" (see CONTEXT.md).
