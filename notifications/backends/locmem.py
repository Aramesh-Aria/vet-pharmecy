"""In-memory SMS backend for tests. Captures sent messages in ``outbox``."""
from .base import BaseSMSBackend

#: list of (phone, message) tuples sent during a test run.
outbox: list[tuple[str, str]] = []


class LocMemSMSBackend(BaseSMSBackend):
    def send(self, phone: str, message: str) -> None:
        outbox.append((phone, message))
