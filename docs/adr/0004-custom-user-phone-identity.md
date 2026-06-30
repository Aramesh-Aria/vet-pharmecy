# Custom User model with phone number as the identity

We define a custom `AUTH_USER_MODEL` from the very first migration. The unique
identity field is the mobile phone number (not username, not email). Owners log
in with phone + password; a one-time code over SMS handles phone verification
and password reset. Email is an optional secondary field.

**Why now:** Swapping Django's User model after migrations exist is famously
disruptive (it touches every FK to the user). It costs almost nothing to set up
on day one and is very expensive to change later — so it is a day-one decision.

**Shape:** a custom user manager keyed on phone; `Owner` profile data hangs off
the user (or the user *is* the Owner with a `role` flag distinguishing Owner
from Staff). Staff are the same user model with elevated permissions / a role,
so the Django admin and auth system work uniformly.
