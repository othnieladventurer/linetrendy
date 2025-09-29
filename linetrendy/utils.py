from .models import Cart
from django.utils.crypto import get_random_string
# utils/email.py
import asyncio
from django.core.mail import send_mail




def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart










async def send_email_async(subject, message, from_email, recipient_list, **kwargs):
    return await asyncio.to_thread(
        send_mail,
        subject,
        message,
        from_email,
        recipient_list,
        **kwargs
    )

