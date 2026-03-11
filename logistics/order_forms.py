from django import forms
from django.core.exceptions import ValidationError
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["address", "destination", "weight", "description"]

    def clean_weight(self):
        w = self.cleaned_data.get("weight")
        if w is None:
            raise ValidationError("Weight is required.")
        if w <= 0:
            raise ValidationError("Weight must be greater than 0.")
        if w > 100000:
            raise ValidationError("Weight is too large.")
        return w