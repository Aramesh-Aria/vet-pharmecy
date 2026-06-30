"""Console SMS backend for development — prints messages instead of sending.

Real Iranian-gateway backends (Phase 2) implement the same ``send`` contract.
"""
import logging

from .base import BaseSMSBackend

logger = logging.getLogger("notifications.sms")


class ConsoleSMSBackend(BaseSMSBackend):
    def send(self, phone: str, message: str) -> None:
        logger.info("SMS -> %s\n%s", phone, message)
        print(f"\n[SMS] to {phone}:\n{message}\n")
