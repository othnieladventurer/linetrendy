from django.urls import path
from . import views
from .views import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
)




app_name = "users"


urlpatterns = [
    path("account/login/", views.custom_login, name="account_login"),
    path("account/signup/", views.CustomSignupView.as_view(), name="account_signup"),
    path("password-reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset-complete/", CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path('logout/', views.custom_logout, name='custom_logout'),
]







