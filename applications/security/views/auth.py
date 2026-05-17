from django.shortcuts import redirect, render
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput)

# ----------------- Cerrar Sesion -----------------
@login_required
def signout(request):
    logout(request)
    return redirect("security:signin")

# # ----------------- Iniciar Sesion -----------------
def signin(request):
    data = {"title": "Login", "title1": "Inicio de Sesión"}
    if request.method == "GET":
        success_messages = messages.get_messages(request)
        return render(request, "security/auth/signin.html", {
            "form": EmailAuthenticationForm(),
            "success_messages": success_messages,
            **data
        })
    else:
        form = EmailAuthenticationForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            # En Django, ModelBackend usa la kwarg que coincide con USERNAME_FIELD (email) o 'username' por compatibilidad
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                return render(request, "security/auth/signin.html", {
                    "form": form,
                    "error": "El usuario o la contraseña son incorrectos",
                    **data
                })
        else:
            return render(request, "security/auth/signin.html", {
                "form": form,
                "error": "Datos invalidos",
                **data
            })