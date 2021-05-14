from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import WZO_User
from .validators import WhitelistEmailValidator
from django.conf import settings

class NewUserForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=200,
        required=True,
        validators=[WhitelistEmailValidator(_('Email-Adresse nicht valide oder Domain nicht zugelassen'),None,settings.ALLOWED_EMAIL_DOMAINS)],
        widget=forms.EmailInput(attrs={'class': 'form-control','id': 'id_email', 'required':True})
    )
    password1 = forms.CharField(
        label=_("Passwort"),
        max_length=150,
        strip=False,
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'id': 'id_password1', 'required':True})
    )
    password2 = forms.CharField(
        label=_("Passwort Bestätigen"),
        max_length=150,
        strip=False,
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control','id': 'id_password2', 'required':True})
    )

    class Meta:
        model = WZO_User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
        labels = {
            "username": _('Benutzername'),
            "first_name": _('Vorname'),
            "last_name": _('Nachname'),
            "email": _('Email')
        }
        widgets = {
            "username": forms.TextInput(attrs={'id': 'id_username', 'required':True, 'class': 'form-control'}),
            "first_name": forms.TextInput(attrs={'disabled': False, 'maxlength': 50, 'id': 'id_first_name', 'required':True, 'class': 'form-control'}),
            "last_name": forms.TextInput(attrs={'disabled': False, 'maxlength': 50, 'id': 'id_last_name', 'required':True, 'class': 'form-control'}),
        }

    def save(self,commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.is_active = False
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Benutzername"),
        max_length=20,
        strip=False,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control','id': 'id_username', 'required':True})
    )
    password = forms.CharField(
        label=_("Passwort"),
        max_length=150,
        strip=False,
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control','id': 'id_password', 'required':True})
    )

    class Meta:
        model = WZO_User

class ResetForm(PasswordResetForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=200,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control','id': 'id_email', 'required':True})
    )

    class Meta:
        model = WZO_User

class NewPasswordForm(PasswordResetForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=200,
        required=True,
        validators=[WhitelistEmailValidator(_('Email-Adresse nicht valide oder Domain nicht zugelassen'),None,settings.ALLOWED_EMAIL_DOMAINS)],
        widget=forms.EmailInput(attrs={'class': 'form-control','id': 'id_email', 'required':True, 'disabled': True})
    )
    password1  = forms.CharField(
        label=_("Passwort"),
        max_length=150,
        strip=False,
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'id': 'id_new1', 'required':True})
    )
    password2 = forms.CharField(
        label=_("Passwort Bestätigen"),
        max_length=150,
        strip=False,
        required=True,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control','id': 'id_new2', 'required':True})
    )

    class Meta:
        model = WZO_User

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label=_("Vorname"),
        max_length=50,
        strip=False,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control','id': 'id_first_name', 'required':True})
    )
    last_name = forms.CharField(
        label=_("Nachname"),
        max_length=50,
        strip=False,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control','id': 'id_last_name', 'required':True})
    )
    email = forms.EmailField(
        label=_("Email"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control','id': 'id_email', 'required':True, 'readonly':'readonly'})
    )
    class Meta:
        model = WZO_User
        fields= ['first_name', 'last_name', 'email']