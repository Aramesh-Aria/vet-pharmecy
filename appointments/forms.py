from django import forms
from django.core.exceptions import ValidationError

from catalog.models import Service
from core.widgets import CategoryDataSelect, JalaliDateInput


class AppointmentRequestForm(forms.Form):
    """Owner picks a subject (one of their Animals *or* Herds), a Service in that
    subject's Animal Category, and a preferred date. The service dropdown is
    filtered to the subject's category client-side (JS) and validated here."""

    subject = forms.ChoiceField(label="حیوان یا گله", widget=CategoryDataSelect)
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True),
        label="خدمت",
        widget=CategoryDataSelect,
    )
    preferred_date = forms.DateField(label="تاریخ پیشنهادی", widget=JalaliDateInput())
    preferred_time_note = forms.CharField(
        label="بازهٔ زمانی پیشنهادی", required=False, max_length=100
    )
    owner_note = forms.CharField(
        label="توضیحات", required=False, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self._subjects = {}  # value -> (kind, instance)
        subject_choices = [("", "— انتخاب کنید —")]
        subject_categories = {}

        if owner is not None:
            animals = list(owner.animals.select_related("animal_category"))
            herds = list(owner.herds.select_related("animal_category"))
            if animals:
                group = []
                for a in animals:
                    value = f"animal:{a.pk}"
                    group.append((value, a.name))
                    self._subjects[value] = ("animal", a)
                    subject_categories[value] = a.animal_category_id
                subject_choices.append(("حیوانات", group))
            if herds:
                group = []
                for h in herds:
                    value = f"herd:{h.pk}"
                    group.append((value, str(h)))
                    self._subjects[value] = ("herd", h)
                    subject_categories[value] = h.animal_category_id
                subject_choices.append(("گله‌ها", group))

        self.fields["subject"].choices = subject_choices
        self.fields["subject"].widget.category_by_value = {
            str(k): v for k, v in subject_categories.items()
        }

        services = Service.objects.filter(is_active=True).select_related("animal_category")
        self.fields["service"].queryset = services
        self.fields["service"].widget.category_by_value = {
            str(s.pk): s.animal_category_id for s in services
        }

    def clean_subject(self):
        value = self.cleaned_data["subject"]
        if value not in self._subjects:
            raise ValidationError("گزینهٔ نامعتبر است.")
        return value

    def clean(self):
        cleaned = super().clean()
        value = cleaned.get("subject")
        service = cleaned.get("service")
        if value and service:
            _, subject = self._subjects[value]
            if service.animal_category_id != subject.animal_category_id:
                self.add_error("service", "این خدمت با دستهٔ انتخاب‌شده همخوانی ندارد.")
        return cleaned

    @property
    def selected_subject(self):
        """Return (kind, instance) for the chosen subject, or (None, None)."""
        value = self.cleaned_data.get("subject")
        return self._subjects.get(value, (None, None))
