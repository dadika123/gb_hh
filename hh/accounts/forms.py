from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm, UserChangeForm

from .models import Account, JobSeeker


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = Account
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "status"
        )

    def __init__(self, *args, **kwargs):
        new_status_choices = kwargs.pop('new_status_choices')
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = new_status_choices
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            field.help_text = ""

    def save(self, commit=True, **kwargs):
        user = self.instance
        if not user.id:
            user.active = False
            user = super().save()
        return user


class UserActivationRegisterForm(forms.Form):
    class Meta:
        model = Account

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.user.active = True
        if commit:
            self.user.save()
        return self.user


class JobSeekerFormUpdate(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].disabled = True
    class Meta:
        model = JobSeeker
        fields = (
            'user',
            'first_name',
            'last_name',
            'patronymic',
            'sex',
            'date_birth',
        )
