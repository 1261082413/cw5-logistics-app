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


class AdminOrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status", "current_lat", "current_lng", "tracking_note"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "current_lat": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "current_lng": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "tracking_note": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_current_lat(self):
        lat = self.cleaned_data.get("current_lat")
        if lat is not None and (lat < -90 or lat > 90):
            raise ValidationError("Latitude must be between -90 and 90.")
        return lat

    def clean_current_lng(self):
        lng = self.cleaned_data.get("current_lng")
        if lng is not None and (lng < -180 or lng > 180):
            raise ValidationError("Longitude must be between -180 and 180.")
        return lng