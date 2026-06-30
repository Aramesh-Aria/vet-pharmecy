# SMS via an Iranian provider, behind a single notification layer

Owners are notified by both email and SMS (appointment confirmed, refill ready,
order ready for pickup, vaccination due). All notifications go through one
internal `notifications` app exposing a single `notify(owner, event, context)`
entry point, with pluggable backends.

- **Email backend:** Django SMTP via a transactional provider.
- **SMS backend:** an Iran-reachable gateway (Kavenegar / SMS.ir / Ghasedak),
  NOT Twilio. SMS also delivers login/verification OTP codes.

**Why a layer:** the choice of SMS gateway, and even whether a given event uses
SMS vs email, will change. Callers should never import a provider SDK directly.

**Consequence:** OTP delivery and notification delivery share the same SMS
backend, so provider downtime affects login — the layer must surface send
failures, not swallow them.
