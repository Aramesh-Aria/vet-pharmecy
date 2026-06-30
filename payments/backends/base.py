"""Payment backend interface (ADR-0005).

A backend turns a :class:`~payments.models.Payment` into a gateway interaction.
The real Iranian-gateway backend (Phase 5) and the launch pay-at-pickup backend
both implement this contract, so swapping backends needs no checkout rework.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StartResult:
    """Outcome of starting a payment.

    ``redirect_url`` is where the Owner is sent to pay (None for backends that
    settle out-of-band, e.g. pay-at-pickup).
    """

    payment_id: int
    redirect_url: str | None = None


class BasePaymentBackend:
    """Subclass and implement :meth:`start` and :meth:`verify`."""

    #: Whether this backend collects money online (vs. settled in person).
    online = False

    def start(self, payment) -> StartResult:
        """Begin payment; persist any gateway authority on *payment*."""
        raise NotImplementedError

    def verify(self, payment, data: dict) -> bool:
        """Confirm a payment from gateway callback *data*. Must be idempotent:
        calling it twice for an already-paid payment returns True without
        double-settling.
        """
        raise NotImplementedError

    def get_redirect_url(self, payment) -> str | None:
        """Where to send the Owner to pay, derived from the stored payment.
        None for out-of-band backends (e.g. pay-at-pickup)."""
        return None
