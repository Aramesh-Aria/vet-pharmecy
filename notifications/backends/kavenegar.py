"""Kavenegar SMS backend — a real Iran-reachable gateway (ADR-0003).

Selected by setting ``SMS_BACKEND`` to this class in production and providing
``SMS_API_KEY`` (and optionally ``SMS_SENDER``). Uses the standard library so no
extra dependency is pulled in. Delivery failures raise
:class:`~notifications.backends.base.SMSDeliveryError`, never silent success —
OTP login depends on it.

NOTE: needs a funded Kavenegar account + line number; verify end-to-end against
the real gateway before launch. Console backend stays the dev default.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

from .base import BaseSMSBackend, SMSDeliveryError

API_URL = "https://api.kavenegar.com/v1/{key}/sms/send.json"
TIMEOUT = 10


class KavenegarSMSBackend(BaseSMSBackend):
    def send(self, phone: str, message: str) -> None:
        api_key = getattr(settings, "SMS_API_KEY", "")
        if not api_key:
            raise SMSDeliveryError("کلید سرویس پیامک تنظیم نشده است (SMS_API_KEY).")

        params = {"receptor": phone, "message": message}
        sender = getattr(settings, "SMS_SENDER", "")
        if sender:
            params["sender"] = sender

        url = API_URL.format(key=api_key)
        data = urllib.parse.urlencode(params).encode()
        try:
            with urllib.request.urlopen(url, data=data, timeout=TIMEOUT) as resp:
                payload = json.loads(resp.read().decode())
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise SMSDeliveryError(f"ارتباط با درگاه پیامک ناموفق بود: {exc}") from exc

        status = payload.get("return", {}).get("status")
        if status != 200:
            message_text = payload.get("return", {}).get("message", "خطای نامشخص")
            raise SMSDeliveryError(f"ارسال پیامک ناموفق بود: {message_text}")
