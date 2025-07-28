from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import *

from .forms import AdminEmailAuthenticationForm
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin 



from django.contrib.admin.sites import AlreadyRegistered, NotRegistered

try:
    admin.site.unregister(CustomUser)
except NotRegistered:
    pass


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    model = CustomUser
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ('email', 'first_name', 'last_name', 'role', 'is_superuser', 'is_staff', 'is_active')
    list_filter = ('role', 'is_superuser', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        ('Login Credentials', {
            'fields': ('email', 'password'),
            'classes': ('tab-login',),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number', 'company'),
            'classes': ('tab-personal',),
        }),
        ('Permissions & Role', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('tab-permissions',),
        }),
        ('Important Dates', {
            'fields': ('last_login',),
            'classes': ('tab-dates',),
        }),
    )

    tabs = [
        ('tab-login', 'Login'),
        ('tab-personal', 'Personal Info'),
        ('tab-permissions', 'Permissions'),
        ('tab-dates', 'Dates'),
    ]

    add_fieldsets = (
        ('Create User', {
            'classes': ('wide', 'tab-login'),
            'fields': ('email', 'password1', 'password2', 'role', 'is_active', 'is_staff', 'is_superuser')
        }),
    )

    





