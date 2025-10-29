from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from .models import Order
from django.urls import reverse







@receiver(post_save, sender=Order)
def send_order_confirmation_email(sender, instance, created, **kwargs):
    if not created:  # only trigger for new orders
        return

    # Determine recipient
    if instance.user:
        recipient_email = instance.user.email
        recipient_name = instance.user.get_full_name() or instance.user.username
    else:
        recipient_email = instance.guest_email
        recipient_name = "Customer"

    if not recipient_email:
        return

    # Build tracking URL (hardcode your domain)
    BASE_URL = getattr(settings, "BASE_URL", "https://www.linetrendy.com")
    if instance.user:
        tracking_path = reverse('shop:order_tracking', args=[instance.order_number])
    else:
        tracking_path = f"{reverse('shop:guest_order_tracking')}?order_number={instance.order_number}"
    tracking_url = f"{BASE_URL}{tracking_path}"

    # Email subject and content
    subject = f"Order Confirmation - #{instance.order_number}"

    plain_text = f"""
Dear {recipient_name},

Thank you for your order!

Order Number: #{instance.order_number}
Total Amount: ${instance.total_amount}
Order Date: {instance.created_at.strftime("%B %d, %Y")}

Track your order here: {tracking_url}

We’ll notify you again once your order has been shipped!

Best regards,
The LineTrendy Team
"""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #dc2626; color: white; padding: 20px; text-align: center; }}
        .content {{ background: #f9f9f9; padding: 20px; }}
        .order-info {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #dc2626; }}
        .footer {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LineTrendy</h1>
            <p>Hair Products for All Hair Types</p>
        </div>
        
        <div class="content">
            <p>Dear {recipient_name},</p>
            
            <p>Thank you for your order! Here are your order details:</p>
            
            <div class="order-info">
                <h3>Order Details</h3>
                <p><strong>Order Number:</strong> #{instance.order_number}</p>
                <p><strong>Total Amount:</strong> ${instance.total_amount}</p>
                <p><strong>Order Date:</strong> {instance.created_at.strftime("%B %d, %Y")}</p>
                <p><strong>Track your order:</strong> <a href="{tracking_url}">{tracking_url}</a></p>
            </div>

            <p>We’ll notify you again once your order has been shipped!</p>
        </div>
        
        <div class="footer">
            <p>Best regards,<br>The LineTrendy Team</p>
            <p>Need help? Contact us at linetrendyllc@gmail.com</p>
        </div>
    </div>
</body>
</html>
"""

    # Send safely
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
        reply_to=['linetrendyllc@gmail.com'],
    )
    email.attach_alternative(html_content, "text/html")

    try:
        email.send(fail_silently=True)
        print(f"✅ Order confirmation email sent to {recipient_email}")
    except Exception as e:
        print(f"⚠️ Failed to send confirmation email to {recipient_email}: {e}")










@receiver(post_save, sender=Order)
def send_order_status_email(sender, instance, created, **kwargs):
    if created:
        return
    
    if instance.user:
        recipient_email = instance.user.email
        recipient_name = instance.user.get_full_name() or instance.user.username
    else:
        recipient_email = instance.guest_email
        recipient_name = "Customer"
    
    if not recipient_email:
        return
    
    status_display = dict(Order.STATUS_CHOICES).get(instance.status, instance.status)
    subject = f"Order Update: Your Order #{instance.order_number} is {status_display}"
    
    # ✅ Call helper functions directly (no `self`)
    plain_text = f"""
Dear {recipient_name},

Your order status has been updated:

Order Number: #{instance.order_number}
Current Status: {status_display}
Total Amount: ${instance.total_amount}
Order Date: {instance.created_at.strftime("%B %d, %Y")}

{get_status_message(instance.status)}

Thank you for choosing LineTrendy for your hair care needs.

Best regards,
The LineTrendy Team
"""
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #dc2626; color: white; padding: 20px; text-align: center; }}
        .content {{ background: #f9f9f9; padding: 20px; }}
        .order-info {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #dc2626; }}
        .status-badge {{ background: #dc2626; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold; }}
        .footer {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LineTrendy</h1>
            <p>Hair Products for All Hair Types</p>
        </div>
        
        <div class="content">
            <p>Dear {recipient_name},</p>
            
            <p>Your order status has been updated:</p>
            
            <div class="order-info">
                <h3>Order Details</h3>
                <p><strong>Order Number:</strong> #{instance.order_number}</p>
                <p><strong>Status:</strong> <span class="status-badge">{status_display}</span></p>
                <p><strong>Total Amount:</strong> ${instance.total_amount}</p>
                <p><strong>Order Date:</strong> {instance.created_at.strftime("%B %d, %Y")}</p>
            </div>
            
            <p>{get_status_message_html(instance.status)}</p>
            
            <p>Thank you for choosing LineTrendy for your hair care needs.</p>
        </div>
        
        <div class="footer">
            <p>Best regards,<br>The LineTrendy Team</p>
            <p>Need help? Contact us at linetrendyllc@gmail.com</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Send both plain text and HTML versions
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
        reply_to=['linetrendyllc@gmail.com'],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)
    
    print(f"Professional email sent to {recipient_email}")


# ✅ Helper functions should not use `self`
def get_status_message(status):
    messages = {
        "placed": "We've received your order and are preparing it for shipment.",
        "shipped": "Your order has been shipped and is on its way to you.",
        "out_for_delivery": "Your order is out for delivery today!",
        "delivered": "Your order has been delivered. We hope you love your products!",
        "cancelled": "Your order has been cancelled as requested.",
        "refunded": "Your refund has been processed.",
    }
    return messages.get(status, "Your order status has been updated.")


def get_status_message_html(status):
    messages = {
        "placed": "We've received your order and are preparing it for shipment. You'll receive another update when your order ships.",
        "shipped": "Your order has been shipped and is on its way to you. You should receive it soon.",
        "out_for_delivery": "Your order is out for delivery today! Please ensure someone is available to receive your package.",
        "delivered": "Your order has been delivered. We hope you love your LineTrendy products!",
        "cancelled": "Your order has been cancelled as requested. If this was a mistake, please contact our support team.",
        "refunded": "Your refund has been processed. The amount will be credited to your original payment method within 5-7 business days.",
    }
    return messages.get(status, "Your order status has been updated.")


