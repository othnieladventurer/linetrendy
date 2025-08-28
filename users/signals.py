# users/signals.py
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from django.core.mail import send_mail
from django.conf import settings



@receiver(user_signed_up)
def send_welcome_email(request, user, **kwargs):
    subject = "Welcome to Linetrendy 🎉"
    message = (
        f"Hi {user.email},\n\n"
        "Thanks for signing up at Linetrendy! We’re excited to have you.\n\n"
        "You can now explore our shop and enjoy exclusive offers.\n\n"
        "Cheers,\nThe Linetrendy Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])





