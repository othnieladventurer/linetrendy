from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail

from django.urls import reverse_lazy
from allauth.account.views import SignupView
from .forms import CustomSignupForm
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

from django.urls import reverse_lazy
from django.contrib import messages
from django import forms
from django.contrib.auth import get_user_model


User = get_user_model()

# from django.contrib.auth import get_user_model
class LoginForm(forms.Form):
    login = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Email or username', 'class': 'input-focus'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'input-focus'})
    )

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('/')  # already logged in

    form = LoginForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            identifier = form.cleaned_data['login']
            password = form.cleaned_data['password']

            try:
                user_obj = User.objects.get(email__iexact=identifier)
                username = user_obj.get_username()
            except User.DoesNotExist:
                username = identifier  # fallback to raw input

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get('next') or '/'
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username/email or password.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    return render(request, 'users/account/login.html', {'form': form})







class CustomSignupView(SignupView):
    template_name = "users/account/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "You have successfully signed up. Check your email for a confirmation link."
        )
        return response

    def form_invalid(self, form):
        # Stay on this template and show form errors
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("shop:index")





class CustomPasswordResetView(PasswordResetView):
    template_name = "users/account/password_reset.html"
    email_template_name = "users/account/password_reset_email.txt"   # plain text fallback
    html_email_template_name = "users/account/password_reset_email.html"  # HTML version
    subject_template_name = "users/account/password_reset_subject.txt"
    success_url = reverse_lazy("users:password_reset_done")

    def form_valid(self, form):
        messages.success(self.request, "Password reset link sent! Check your email.")
        return super().form_valid(form)




class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/account/password_reset_done.html"




class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "users/account/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been reset successfully!")
        return super().form_valid(form)



class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "users/account/password_reset_complete.html"




def access_denied_view(request):
    return render(request, 'dashboard/partials/access_denied.html')




def custom_logout(request):
    logout(request)
    return redirect('shop:index')
