from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail

from django.urls import reverse_lazy
from allauth.account.views import SignupView
from .forms import CustomSignupForm

# from django.contrib.auth import get_user_model


def custom_login(request):
    # Redirect authenticated users away from the login page
    if request.user.is_authenticated:
        return redirect('/')  # or a named url like: return redirect('shop:index')

    if request.method == 'POST':
        identifier = (request.POST.get('login') or '').strip()
        password = (request.POST.get('password') or '').strip()

        if not identifier or not password:
            messages.error(request, 'Both username/email and password are required.')
            return render(request, 'users/account/login.html')

        # With USERNAME_FIELD='email', passing username=identifier is fine (identifier can be the email)
        user = authenticate(request, username=identifier, password=password)
        if user is not None:
            login(request, user)
            pending_slug = request.session.pop('pending_cart_add', None)
            if pending_slug:
                return redirect('cart:add', plan_slug=pending_slug)
            return redirect('shop:index')

        messages.error(request, 'Invalid username/email or password.')
        return render(request, 'users/account/login.html')

    # GET
    return render(request, 'users/account/login.html')




def send_welcome_email(email: str) -> None:
    subject = "Welcome to Our Platform!"
    message = (
        "Hello,\n\n"
        "Thank you for signing up! We're excited to have you on board.\n\n"
        "Best regards,\n"
        "Saasiskey LLC"
    )
    sender_email = getattr(settings, "DEFAULT_FROM_EMAIL", getattr(settings, "EMAIL_HOST_USER", None))
    send_mail(subject, message, sender_email, [email], fail_silently=False)





class CustomSignupView(SignupView):
    form_class = CustomSignupForm
    template_name = "users/account/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "You have successfully signed up. Check your email for a confirmation link and welcome message."
        )
        return response

    def get_success_url(self):
        return reverse_lazy("users:account_login")  #





def access_denied_view(request):
    return render(request, 'dashboard/partials/access_denied.html')




def custom_logout(request):
    logout(request)
    return redirect('shop:index')
