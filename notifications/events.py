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
        "sms": "درخواست تکرار نسخهٔ شماره {refill.pk} تأیید شد؛ اکنون می‌توانید داروی خود را از بخش نسخه‌ها سفارش دهید.",
        "email_subject": "تأیید تکرار نسخه",
        "email_body": "{name} عزیز،\nدرخواست تکرار نسخهٔ شماره {refill.pk} تأیید شد. "
                      "می‌توانید داروی خود را از بخش «نسخه‌های من» سفارش دهید.",
    },
    "appointment_requested": {
        "sms": "درخواست نوبت شماره {appointment.pk} ثبت شد و در انتظار تأیید است.",
        "email_subject": "ثبت درخواست نوبت",
        "email_body": "{name} عزیز،\nدرخواست نوبت شماره {appointment.pk} ثبت شد.",
    },
    "appointment_confirmed": {
        "sms": "نوبت شماره {appointment.pk} تأیید شد. زمان را در پنل کاربری ببینید.",
        "email_subject": "تأیید نوبت",
        "email_body": "{name} عزیز،\nنوبت شماره {appointment.pk} تأیید شد.",
    },
    "appointment_cancelled": {
        "sms": "نوبت شماره {appointment.pk} لغو شد.",
        "email_subject": "لغو نوبت",
        "email_body": "{name} عزیز،\nنوبت شماره {appointment.pk} لغو شد.",
    },
    "appointment_completed": {
        "sms": "نوبت شماره {appointment.pk} انجام شد. از مراجعهٔ شما سپاسگزاریم.",
        "email_subject": "انجام نوبت",
        "email_body": "{name} عزیز،\nنوبت شماره {appointment.pk} انجام شد.",
    },
    "vaccination_due": {
        "sms": "یادآوری: واکسن «{vaccination.vaccine_name}» برای {vaccination.animal.name} نزدیک است.",
        "email_subject": "یادآوری واکسیناسیون",
        "email_body": "{name} عزیز،\nموعد واکسن «{vaccination.vaccine_name}» برای "
                      "{vaccination.animal.name} نزدیک است.",
    },
}
