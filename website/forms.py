import re

from django import forms

from .models import ContactMessage

PHONE_PATTERN = re.compile(r"^[0-9+()\-\s]{0,30}$")


class ContactForm(forms.ModelForm):
    message = forms.CharField(min_length=10, max_length=3000)

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "topic", "message"]

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not PHONE_PATTERN.match(phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone