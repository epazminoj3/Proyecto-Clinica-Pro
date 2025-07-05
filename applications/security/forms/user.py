import re
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from applications.security.models import User, Module

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "dni",
            "phone",
            "direction",
            "image",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        ]
        error_messages = {

            "username": {
                "unique": "Ya existe un usuario con este nombre.",
            },
        }
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Ingrese nombre de usuario",
                "id": "id_username",
                "class": "form-input",
            }),

            "email": forms.EmailInput(attrs={
                "placeholder": "Ingrese correo electrónico",
                "id": "id_email",
                "class": "form-input",
            }),

            "first_name": forms.TextInput(attrs={
                "placeholder": "Ingrese nombre",
                "id": "id_first_name",
                "class": "form-input",
            }),

            "last_name": forms.TextInput(attrs={
                "placeholder": "Ingrese apellido",
                "id": "id_last_name",
                "class": "form-input",
            }),

            "dni": forms.TextInput(attrs={
                "placeholder": "Ingrese cédula o RUC",
                "id": "id_dni",
                "class": "form-input",
            }),

            "phone": forms.TextInput(attrs={
                "placeholder": "Ingrese teléfono",
                "id": "id_phone",
                "class": "form-input",
            }),

            "direction": forms.Textarea(attrs={
                "placeholder": "Ingrese dirección completa",
                "id": "id_direction",
                "class": "form-textarea",
                "rows": 3,
            }),

            "image": forms.FileInput(attrs={
                "id": "id_image",
                "class": "form-file-input",
                "accept": "image/*",
            }),

            "is_active": forms.CheckboxInput(attrs={
                "id": "id_is_active",
                "class": "form-checkbox",
            }),

            "is_staff": forms.CheckboxInput(attrs={
                "id": "id_is_staff",
                "class": "form-checkbox",
            }),

            "is_superuser": forms.CheckboxInput(attrs={
                "id": "id_is_superuser",
                "class": "form-checkbox",
            }),

            "groups": forms.CheckboxSelectMultiple(attrs={
                "class": "form-checkbox-list",
            }),

            "user_permissions": forms.CheckboxSelectMultiple(attrs={
                "class": "form-checkbox-list",
            }),
        }
        labels = {
            "username": "Nombre de Usuario",
            "email": "Correo Electrónico",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "dni": "Cédula o RUC",
            "phone": "Teléfono",
            "direction": "Dirección",
            "image": "Foto de Perfil",
            "is_active": "¿Usuario Activo?",
            "is_staff": "¿Es Personal/Staff?",
            "is_superuser": "¿Es Superusuario?",
            "groups": "Grupos de Usuario",
            "user_permissions": "Permisos de Usuario",
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        return username.upper()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Check if email already exists for another user
        if self.instance.pk:
            # Editing existing user
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Ya existe un usuario con este correo electrónico.")
        else:
            # Creating new user
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Ya existe un usuario con este correo electrónico.")
        return email.lower()

    def clean_dni(self):
        dni = self.cleaned_data.get("dni")
        if dni:
            # Basic DNI validation (can be customized per country)
            if not dni.isdigit() or len(dni) < 8:
                raise forms.ValidationError("El DNI debe contener al menos 8 dígitos.")
        return dni

class UserCreateForm(BaseUserCreationForm):
    """Form for creating new users with password fields"""
    
    class Meta:
        model = User
        fields = [
            "username",
            "password1",
            "password2",
        ]
        error_messages = {
            "username": {
                "unique": "Ya existe un usuario con este nombre.",
            },
        }
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Ingrese nombre de usuario",
                "id": "id_username",
                "class": "form-input",
            }),

            "password1": forms.PasswordInput(attrs={
                "placeholder": "Ingrese contraseña",
                "id": "id_password1",
                "class": "form-input",
            }),

            "password2": forms.PasswordInput(attrs={
                "placeholder": "Confirme contraseña",
                "id": "id_password2",
                "class": "form-input",
            }),
        }
        labels = {
            "username": "Nombre de Usuario",
            "password1": "Contraseña",
            "password2": "Confirmación de Contraseña",
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        return username.upper()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este correo electrónico.")
        return email.lower() if email else None