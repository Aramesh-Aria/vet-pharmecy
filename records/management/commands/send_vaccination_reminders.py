"""Send reminders for vaccinations coming due. Run from cron (PLAN §4)::

    python manage.py send_vaccination_reminders [--days N]
"""
from django.core.management.base import BaseCommand

from records.services import send_due_reminders


class Command(BaseCommand):
    help = "ارسال یادآوری برای واکسیناسیون‌های نزدیک به موعد"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="بازهٔ یادآوری به روز (پیش‌فرض از تنظیمات).",
        )

    def handle(self, *args, **options):
        sent = send_due_reminders(window_days=options["days"])
        self.stdout.write(self.style.SUCCESS(f"{sent} یادآوری ارسال شد."))
