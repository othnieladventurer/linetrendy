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
class CustomUserAdmin(ModelAdmin):  # Use Unfold's ModelAdmin
    model = CustomUser
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ('email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active')
    list_filter = ('is_superuser', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        ('Login Credentials', {
            'fields': ('email', 'password'),
            'classes': ('tab-login',),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture'),
            'classes': ('tab-personal',),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
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
            'fields': ('email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    # Optional: ensure password change is available via unfold
    def get_fieldsets(self, request, obj=None):
        return super().get_fieldsets(request, obj=obj)
    






