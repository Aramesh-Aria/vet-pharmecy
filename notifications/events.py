"""Notification event catalogue.

Each event maps to the SMS text and email subject/body used to render it.
Channels actually sent are decided per Owner preference in ``service.notify``.
New events (appointment confirmed/declined, order ready, refill ready,
vaccination due) are added here as later phases land.
"""

# event key -> dict(sms, email_subject, email_body). Bodies are str.format
# templates filled from the notify() context.
EVENTS = {
    "welcome": {
        "sms": "به کلینیک و داروخانه دامپزشکی خوش آمدید، {name} عزیز.",
        "email_subject": "خوش آمدید",
        "email_body": "{name} عزیز،\nحساب شما با موفقیت ساخته شد.",
    },
}
