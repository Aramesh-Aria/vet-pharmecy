# Farsi-first, RTL layout, and the Jalali calendar

The Practice and its customers are Persian-speaking. The site is built Farsi-first
with a right-to-left layout, not retrofitted onto an English LTR base.

**What this commits us to:**

- **RTL by default.** Base templates set `dir="rtl"` / `lang="fa"`; all CSS uses
  logical properties (`margin-inline-start`, not `margin-left`) so layout is
  direction-correct. A Farsi web font (e.g. Vazirmatn) is bundled.
- **Jalali (Shamsi) calendar.** Dates shown to Owners use the Jalali calendar via
  `jdatetime` / `django-jalali`, while the database stores standard datetimes.
  Appointment dates, vaccination due-dates, and order timestamps all render
  Jalali.
- **Persian digits and number/price formatting** in the UI.
- **i18n plumbing** (`gettext`, `LocaleMiddleware`) is wired from the start so a
  second language could be added later, but only Farsi is designed for now.

**Consequence — supersedes part of the notification decision:** SMS must go
through an Iran-reachable provider (e.g. Kavenegar, SMS.ir, Ghasedak), not
Twilio, which does not reliably deliver to Iranian numbers. See ADR-0003.
