from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import Profile


def validate_name(value):
    if value.isdigit():
        raise ValidationError("Name cannot be numbers.")


class SignUpForm(forms.Form):
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, widget=forms.RadioSelect)
    username = forms.CharField(max_length=30)
    email = forms.EmailField()
    first_name = forms.CharField(validators=[validate_name])
    last_name = forms.CharField(validators=[validate_name])
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("password1") != cleaned.get("password2"):
            raise ValidationError("Passwords do not match.")

        if User.objects.filter(username=cleaned.get("username")).exists():
            raise ValidationError("Username already exists.")

        return cleaned


class LoginForm(forms.Form):
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, widget=forms.RadioSelect)
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        user = authenticate(
            username=cleaned.get("username"),
            password=cleaned.get("password"),
        )

        if user is None:
            raise ValidationError("Invalid username or password.")

        if user.profile.role != cleaned.get("role"):
            raise ValidationError("Role mismatch.")

        cleaned["user"] = user
        return cleaned