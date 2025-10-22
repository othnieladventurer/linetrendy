from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import *

from .forms import AdminEmailAuthenticationForm
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin 
from django.contrib.auth.forms import AdminPasswordChangeForm
from django import forms
from django.contrib.auth import get_user_model


from django.contrib.admin.sites import AlreadyRegistered, NotRegistered

try:
    admin.site.unregister(CustomUser)
except NotRegistered:
    pass


CustomUser = get_user_model()


# --- Create User Form ---
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control rounded-md border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50",
                "placeholder": "Enter password",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control rounded-md border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50",
                "placeholder": "Confirm password",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "profile_picture",
            "is_active",
            "is_staff",
            "is_superuser",
        )
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control rounded-md border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50",
                    "placeholder": "Email address",
                }
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control rounded-md border-gray-300"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control rounded-md border-gray-300"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control rounded-md border-gray-300"}
            ),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# --- Edit User Form ---
class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "profile_picture",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control rounded-md border-gray-300 focus:border-indigo-500"
                }
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control rounded-md border-gray-300"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control rounded-md border-gray-300"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control rounded-md border-gray-300"}
            ),
        }


# --- Admin Registration ---
@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_superuser",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_superuser", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        ("Login Credentials", {"fields": ("email", "password"), "classes": ("tab-login",)}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone_number", "profile_picture"), "classes": ("tab-personal",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"), "classes": ("tab-permissions",)}),
        ("Important Dates", {"fields": ("last_login",), "classes": ("tab-dates",)}),
    )

    tabs = [
        ("tab-login", "Login"),
        ("tab-personal", "Personal Info"),
        ("tab-permissions", "Permissions"),
        ("tab-dates", "Dates"),
    ]

    add_fieldsets = (
        ("Create User", {
            "classes": ("wide", "tab-login"),
            "fields": ("email", "password1", "password2", "is_active", "is_staff", "is_superuser"),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """Use correct form depending on add/edit."""
        defaults = {}
        if obj is None:
            defaults["form"] = self.add_form
        else:
            defaults["form"] = self.form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)




