"""SMS backend interface (ADR-0003).

The real backend talks to an Iran-reachable gateway (Kavenegar / SMS.ir /
Ghasedak) — never Twilio. Callers never import a gateway SDK directly; they go
through :func:`notifications.sms.send_sms`, which loads the configured backend.
"""


class SMSDeliveryError(Exception):
    """Raised when an SMS cannot be delivered. Must not be swallowed: OTP login
    depends on SMS, so failures have to surface (ADR-0003)."""


class BaseSMSBackend:
    def send(self, phone: str, message: str) -> None:
        raise NotImplementedError
