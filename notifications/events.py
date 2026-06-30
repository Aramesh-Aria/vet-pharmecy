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
    "order_placed": {
        "sms": "سفارش شماره {order.pk} ثبت شد و در حال بررسی است.",
        "email_subject": "ثبت سفارش",
        "email_body": "{name} عزیز،\nسفارش شماره {order.pk} ثبت شد.",
    },
    "order_approved": {
        "sms": "سفارش شماره {order.pk} تأیید شد.",
        "email_subject": "تأیید سفارش",
        "email_body": "{name} عزیز،\nسفارش شماره {order.pk} تأیید شد.",
    },
    "order_ready": {
        "sms": "سفارش شماره {order.pk} آمادهٔ تحویل در داروخانه است.",
        "email_subject": "آماده تحویل",
        "email_body": "{name} عزیز،\nسفارش شماره {order.pk} آمادهٔ تحویل است.",
    },
    "refill_approved": {
        "sms": "درخواست تکرار نسخهٔ شماره {refill.pk} تأیید و قیمت‌گذاری شد.",
        "email_subject": "تأیید تکرار نسخه",
        "email_body": "{name} عزیز،\nدرخواست تکرار نسخهٔ شماره {refill.pk} تأیید شد.",
    },
    "refill_ready": {
        "sms": "تکرار نسخهٔ شماره {refill.pk} آمادهٔ تحویل در داروخانه است.",
        "email_subject": "آماده تحویل",
        "email_body": "{name} عزیز،\nتکرار نسخهٔ شماره {refill.pk} آمادهٔ تحویل است.",
    },
}
