import stripe
import json
import threading
import logging
import asyncio

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from .models import *
from .models import Cart, CartItem, Discount, ShippingMethod
from django.urls import reverse  
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from .utils import get_cart

from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db.models import Q
from django.core.mail import EmailMessage, get_connection
from .utils import send_email_async
from .models import Newsletter, Testimonial




logger = logging.getLogger(__name__)

# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY







@csrf_exempt
def index(request):
    # Handle AJAX newsletter subscription
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse({"success": False, "message": "Please enter an email."})

            obj, created = Newsletter.objects.get_or_create(email=email)
            if not created:
                return JsonResponse({"success": False, "message": "Already subscribed."})

            return JsonResponse({"success": True, "message": "Subscribed successfully!"})
        except Exception as e:
            return JsonResponse({"success": False, "message": "Something went wrong."})

    # Normal GET request
    product = Product.objects.all().order_by('-created_at')
    category = Category.objects.all()

    testimonial = Testimonial.objects.all()

    context = {
        'products': product[:8],
        'categories': category,
        'testimonials': testimonial
    }
    return render(request, 'linetrendy/index.html', context)


    


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    context = {
        'product': product,
  
    }
    return render(request, 'linetrendy/product_detail.html', context)




def shop(request):
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()

    # Search
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # Category filter
    category_id = request.GET.get('category')
    if category_id:  # only filter if category is present
        try:
            category_id = int(category_id)
            products = products.filter(category__id=category_id)
        except ValueError:
            category_id = None  # fallback to all products
    else:
        category_id = None  # no category selected, show all

    # Sorting
    sort = request.GET.get('sort')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'search_query': query,
        'sort_option': sort,
    }

    return render(request, 'linetrendy/shop.html', context)








def cart(request):
    """Display and update the shopping cart with HTMX-friendly promo code support."""

    # -------------------------
    # 1. Get or create user's cart (respecting user OR session)
    # -------------------------
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        cart = Cart.objects.filter(session_key=session_key).first()
        if not cart:
            cart = Cart.objects.create(session_key=session_key)

    # -------------------------
    # 2. Get cart items and subtotal
    # -------------------------
    cart_items = cart.items.all()  # use related_name="items"

    total_price = sum(
        (Decimal(str(item.product.price)) * Decimal(item.quantity))
        for item in cart_items
    ) or Decimal("0.00")
    total_price = Decimal(total_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    shipping_fee = Decimal("0.00")

    # -------------------------
    # 3. Handle shipping method
    # -------------------------
    if request.method == "POST" and request.POST.get("shipping_method"):
        shipping_id = request.POST.get("shipping_method")
        if shipping_id:
            shipping_method = get_object_or_404(ShippingMethod, id=shipping_id)
            cart.shipping_method = shipping_method
            cart.save()
            shipping_fee = shipping_method.fee
    elif cart.shipping_method:
        shipping_fee = cart.shipping_method.fee

    # -------------------------
    # 4. Calculate discount base
    # -------------------------
    discount_base = total_price + shipping_fee

    # -------------------------
    # 5. Promo code handling
    # -------------------------
    promo_message = ""
    promo_error = ""
    discount = Decimal("0.00")
    discount_type = None
    applied_promo_code = request.session.get("promo_code")

    if request.method == "POST":
        promo_code = request.POST.get("promo_code", "").strip()
        remove_promo = request.POST.get("remove_promo")

        if promo_code:
            try:
                promo = Discount.objects.get(code__iexact=promo_code, active=True)
                if request.user.is_authenticated:
                    already_used = DiscountUsage.objects.filter(
                        user=request.user, discount=promo
                    ).exists()
                    if already_used:
                        promo_error = "You have already used this promo code."
                        request.session.pop("promo_code", None)
                        applied_promo_code = None
                    else:
                        request.session["promo_code"] = promo.code
                        applied_promo_code = promo.code
                        discount = promo.get_discount(discount_base)
                        discount_type = "amount" if promo.amount else "percent"
                        promo_message = "Promo code applied successfully!"
                else:
                    promo_error = "You must be logged in to use this promo code."
                    request.session.pop("promo_code", None)
                    applied_promo_code = None
            except Discount.DoesNotExist:
                request.session.pop("promo_code", None)
                applied_promo_code = None
                promo_error = "Invalid or expired promo code."

        elif remove_promo:
            request.session.pop("promo_code", None)
            applied_promo_code = None
            discount = Decimal("0.00")
            discount_type = None
            promo_message = "Promo code removed."

    elif applied_promo_code:
        promo = Discount.objects.filter(code__iexact=applied_promo_code, active=True).first()
        if promo:
            discount = promo.get_discount(discount_base)
            discount_type = "amount" if promo.amount else "percent"

    # -------------------------
    # 6. Calculate final total
    # -------------------------
    discount = Decimal(discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    final_total = (total_price + shipping_fee - discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if final_total < 0:
        final_total = Decimal("0.00")

    # -------------------------
    # 7. Prepare context
    # -------------------------
    context = {
        "cart": cart,
        "cart_items": cart_items,
        "total_price": total_price,
        "shipping_fee": shipping_fee,
        "discount": discount,
        "discount_type": discount_type,
        "final_total": final_total,
        "require_shipping_address": True,
        "shipping_methods": ShippingMethod.objects.all(),
        "applied_promo_code": applied_promo_code,
        "promo_message": promo_message,
        "promo_error": promo_error,
    }

    # -------------------------
    # 8. Render response
    # -------------------------
    if request.headers.get("HX-Request"):
        return render(request, "linetrendy/partials/cart_totals.html", context)

    return render(request, "linetrendy/cart.html", context)









def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        cart = get_cart(request)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        # HTMX response → replace button
        if request.headers.get("HX-Request") == "true":
            cart_count = sum(item.quantity for item in cart.items.all())
            return render(
                request,
                "linetrendy/partials/cart_button_added.html",
                {"product": product, "cart_count": cart_count}
            )

        return redirect(request.META.get("HTTP_REFERER", "/"))

    return redirect("/")



def update_cart_quantity(request, item_id):
    cart = get_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    action = request.POST.get('action')

    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        cart_item.quantity = max(1, cart_item.quantity - 1)

    cart_item.save()
    cart_items = cart.items.select_related('product').all()

    # totals
    subtotal = sum(i.product.price * i.quantity for i in cart_items)
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else Decimal("0.00")
    discount = cart.discount.get_discount(subtotal) if cart.discount and cart.discount.active else Decimal("0.00")
    final_total = max(subtotal + shipping_fee - discount, Decimal("0.00"))
    cart_count = sum(i.quantity for i in cart_items)

    # Determine if shipping is required (subtotal <= 35)
    require_shipping_address = True


    context = {
        "cart_item": cart_item,
        "cart_items": cart_items,
        "cart": cart,
        "total_price": subtotal,
        "shipping_methods": ShippingMethod.objects.all(),
        "shipping_fee": shipping_fee,
        "discount": discount,
        "final_total": final_total,
        "cart_count": cart_count,
        "require_shipping_address": require_shipping_address,  # ✅ add this
    }

    html = render_to_string("linetrendy/partials/cart_updated_htmx.html", context, request=request)
    return HttpResponse(html)





def remove_from_cart(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()

    cart_items = cart.items.all()
    total_price = sum(i.product.price * i.quantity for i in cart_items)
    shipping_fee = cart.shipping_method.get_fee(total_price) if cart.shipping_method else 0
    discount = cart.discount.get_discount(total_price) if cart.discount and cart.discount.active else 0
    final_total = max(total_price + shipping_fee - discount, 0)
    cart_count = sum(i.quantity for i in cart_items)

    context = {
        "cart": cart,
        "cart_items": cart_items,
        "total_price": total_price,
        "shipping_fee": shipping_fee,
        "discount": discount,
        "final_total": final_total,
        "cart_count": cart_count,
        "require_shipping_address": True, 
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "linetrendy/partials/cart_updated_htmx.html", context)

    return redirect("shop:cart")





def checkout(request):
    cart = get_cart(request)
    cart_items = cart.items.select_related('product')

    if not cart_items.exists():
        return redirect("shop:cart")

    subtotal = sum((item.product.price if item.product else 0) * item.quantity for item in cart_items)
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else Decimal("0.00")
    
    # FIX: Get discount from session instead of cart.discount
    applied_promo_code = request.session.get("promo_code")
    discount = Decimal("0.00")
    
    if applied_promo_code:
        try:
            promo = Discount.objects.filter(code__iexact=applied_promo_code, active=True).first()
            if promo:
                # For checkout, calculate discount on subtotal + shipping (same as cart view)
                discount_base = subtotal + shipping_fee
                discount = promo.get_discount(discount_base)
                
                # Check if user has already used this promo (for authenticated users)
                if request.user.is_authenticated:
                    already_used = DiscountUsage.objects.filter(
                        user=request.user, discount=promo
                    ).exists()
                    if already_used:
                        discount = Decimal("0.00")
                        request.session.pop("promo_code", None)
        except Discount.DoesNotExist:
            request.session.pop("promo_code", None)
    
    final_total = max(subtotal + shipping_fee - discount, Decimal("0.00"))

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        intent = stripe.PaymentIntent.create(
            amount=int((final_total.quantize(Decimal("0.01"))) * 100),
            currency="usd",
            automatic_payment_methods={"enabled": True},
        )
    except Exception as e:
        logger.error(f"Stripe PaymentIntent creation failed: {e}")
        return HttpResponse("Payment service error. Please try again.", status=500)

    if request.method == "POST":
        payment_intent_id = intent.id
        selected_address_id = request.POST.get("shipping_address")

        try:
            with transaction.atomic():
                # --- Create Order ---
                if request.user.is_authenticated:
                    order = Order.objects.create(
                        user=request.user,
                        cart=cart,
                        total_amount=final_total,
                        payment_intent_id=payment_intent_id,
                        shipping_fee=shipping_fee,
                        discount_amount=discount,
                    )

                    if selected_address_id:
                        address = ShippingAddress.objects.get(id=selected_address_id, user=request.user)
                        address.order = order
                        address.save()
                    else:
                        ShippingAddress.objects.create(
                            user=request.user,
                            order=order,
                            full_name=request.POST.get("full_name"),
                            line1=request.POST.get("line1"),
                            line2=request.POST.get("line2"),
                            city=request.POST.get("city"),
                            state=request.POST.get("state"),
                            postal_code=request.POST.get("postal_code"),
                            country=request.POST.get("country"),
                            phone=request.POST.get("phone"),
                        )
                    email_to = request.user.email

                else:
                    guest_email = request.POST.get("email")
                    if not guest_email:
                        return HttpResponse("Guest email is required", status=400)

                    order = Order.objects.create(
                        user=None,
                        guest_email=guest_email,
                        cart=cart,
                        total_amount=final_total,
                        payment_intent_id=payment_intent_id,
                        shipping_fee=shipping_fee,
                        discount_amount=discount,
                    )

                    ShippingAddress.objects.create(
                        order=order,
                        full_name=request.POST.get("full_name"),
                        line1=request.POST.get("line1"),
                        line2=request.POST.get("line2"),
                        city=request.POST.get("city"),
                        state=request.POST.get("state"),
                        postal_code=request.POST.get("postal_code"),
                        country=request.POST.get("country"),
                        phone=request.POST.get("phone"),
                    )

                    request.session["guest_email"] = guest_email
                    email_to = guest_email

                # --- Build Tracking URL using request domain (FIX) ---
                if request.user.is_authenticated:
                    tracking_path = reverse('shop:order_tracking', args=[order.order_number])
                else:
                    tracking_path = f"{reverse('shop:guest_order_tracking')}?order_number={order.order_number}"

                tracking_url = request.build_absolute_uri(tracking_path)

                # --- Create Order Items ---
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product if item.product else None,
                        product_name=item.product.name if item.product else getattr(item, 'product_name', "Unknown Product"),
                        quantity=item.quantity,
                        price=item.product.price if item.product else getattr(item, 'price', 0),
                    )

                # --- Clear Cart and Session Discount ---
                cart.items.all().delete()
                cart.shipping_method = None
                cart.save()
                
                # Clear the promo code from session after successful order
                if 'promo_code' in request.session:
                    # Record discount usage for authenticated users
                    if request.user.is_authenticated and applied_promo_code:
                        try:
                            promo = Discount.objects.get(code__iexact=applied_promo_code)
                            DiscountUsage.objects.create(user=request.user, discount=promo)
                        except Discount.DoesNotExist:
                            pass
                    
                    del request.session['promo_code']

                # --- Save payment intent in session ---
                request.session["last_payment_intent_id"] = payment_intent_id

                return redirect("shop:checkout_success")

        except Exception as e:
            logger.error(f"Checkout failed: {e}")
            return HttpResponse("Internal Server Error. Please contact support.", status=500)

    context = {
        "cart": cart,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "discount": discount,
        "final_total": final_total,
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
        "client_secret": intent.client_secret,
        "saved_addresses": request.user.addresses.all() if request.user.is_authenticated else [],
    }
    return render(request, "linetrendy/checkout.html", context)





from django.core.mail import get_connection, EmailMultiAlternatives

def checkout_success(request):
    last_order_intent = request.session.get("last_payment_intent_id")
    if not last_order_intent:
        return HttpResponse("No recent order found.", status=400)

    try:
        # Get the order by payment_intent_id
        order = Order.objects.get(payment_intent_id=last_order_intent)

        # Determine email recipient
        email_to = None
        if order.guest_email:
            email_to = order.guest_email
        elif order.user and order.user.email:
            email_to = order.user.email

        if not email_to:
            logger.warning(f"No valid email for order {order.order_number}")
            return HttpResponse("No valid email found for order.", status=400)

    except Order.DoesNotExist:
        return HttpResponse("Order not found.", status=404)

    # Calculate totals
    order_items = order.items.select_related('product').all()
    subtotal = sum(item.price * item.quantity for item in order_items)
    shipping_fee = order.shipping_fee
    discount = order.discount_amount
    final_total = max(subtotal + shipping_fee - discount, Decimal("0.00"))

    # Build absolute tracking URL
    if order.user:
        tracking_path = reverse('shop:order_tracking', args=[order.order_number])
    else:
        tracking_path = f"{reverse('shop:guest_order_tracking')}?order_number={order.order_number}"
    tracking_url = request.build_absolute_uri(tracking_path)

    # Email content using professional HTML design
    email_subject = f"Order Confirmation - {order.order_number}"

    plain_text = f"""
Dear {order.user.get_full_name() if order.user else 'Customer'},

Thank you for your order!

Order Number: #{order.order_number}
Total Amount: ${final_total}

You can track your order here: {tracking_url}

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
            <p>Dear {order.user.get_full_name() if order.user else 'Customer'},</p>
            
            <p>Thank you for your order! Here are your order details:</p>
            
            <div class="order-info">
                <h3>Order Details</h3>
                <p><strong>Order Number:</strong> #{order.order_number}</p>
                <p><strong>Total Amount:</strong> ${final_total}</p>
                <p><strong>Tracking URL:</strong> <a href="{tracking_url}">{tracking_url}</a></p>
            </div>
        </div>
        
        <div class="footer">
            <p>Best regards,<br>The LineTrendy Team</p>
            <p>Need help? Contact us at linetrendyllc@gmail.com</p>
        </div>
    </div>
</body>
</html>
"""

    # ✅ Safe email sending with long timeout and no checkout crash
    try:
        logger.info(f"Sending order confirmation to {email_to} for order {order.order_number}")

        connection = get_connection(
            fail_silently=True,
            timeout=getattr(settings, "EMAIL_TIMEOUT", 60),  # long timeout (default 60s)
        )

        email = EmailMultiAlternatives(
            subject=email_subject,
            body=plain_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_to],
            connection=connection,
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)  # ✅ Don't block checkout success

        logger.info(f"Confirmation email sent successfully (or safely skipped) to {email_to}")

    except Exception as e:
        logger.error(f"Email sending failed for order {order.order_number} to {email_to}: {e}", exc_info=True)

    # Clear session safely
    request.session.pop("last_payment_intent_id", None)
    request.session.pop("guest_email", None)

    # Render success page
    context = {
        "order": order,
        "order_items": order_items,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "discount": discount,
        "final_total": final_total,
        "tracking_url": tracking_url,
    }
    return render(request, "linetrendy/checkout_success.html", context)






@csrf_exempt
def store_payment_intent(request):
    """Store payment intent ID and guest email in session."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            if "payment_intent_id" in data:
                request.session["last_payment_intent_id"] = data["payment_intent_id"]
            if "guest_email" in data:
                request.session["guest_email"] = data["guest_email"]
            return HttpResponse("OK")
        except Exception as e:
            logger.error(f"Failed to store payment intent: {e}")
            return HttpResponse("Error storing payment intent", status=500)
    return HttpResponse("Method not allowed", status=405)

    


def order_receipt(request, order_number):
    # Fetch the order
    order = get_object_or_404(Order, order_number=order_number)
    order_items = order.items.select_related('product').all()

    context = {
        "order": order,
        "order_items": order_items,
        "subtotal": sum(item.price * item.quantity for item in order_items),
        "shipping_fee": order.shipping_fee,
        "discount": order.discount_amount,
        "final_total": order.total_amount,
    }
    return render(request, "linetrendy/order_receipt.html", context)




@login_required
def account_page(request):
    # Fetch orders for the logged-in user
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Paginate: 10 orders per page
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    # Fetch user's shipping addresses
    addresses = ShippingAddress.objects.filter(user=request.user).order_by('-id')

    # Handle profile update
    if request.method == "POST" and 'profile_update' in request.POST:
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.phone = request.POST.get("phone", user.phone)
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("shop:account_page")  # reload the page to reflect changes

    # Handle adding/updating shipping address
    if request.method == "POST" and 'address_form' in request.POST:
        address_id = request.POST.get("address_id")
        if address_id:  # Update existing
            address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
        else:  # Add new
            address = ShippingAddress(user=request.user)

        # Update fields
        address.full_name = request.POST.get("full_name")
        address.line1 = request.POST.get("line1")
        address.line2 = request.POST.get("line2", "")
        address.city = request.POST.get("city")
        address.state = request.POST.get("state")
        address.postal_code = request.POST.get("postal_code")
        address.country = request.POST.get("country", "US")
        address.phone = request.POST.get("phone", "")
        address.save()
        messages.success(request, "Address saved successfully.")
        return redirect("shop:account_page")  # reload page

    # Handle deleting shipping address
    if request.method == "POST" and 'delete_address_id' in request.POST:
        address = get_object_or_404(ShippingAddress, id=request.POST.get("delete_address_id"), user=request.user)
        address.delete()
        messages.success(request, "Address deleted successfully.")
        return redirect("shop:account_page")

    context = {
        "orders": orders,
        "addresses": addresses,
        "user": request.user,  # template can access user's fields
    }
    return render(request, "linetrendy/account_page.html", context)





@login_required
def add_address(request):
    if request.method == 'POST':
        ShippingAddress.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            line1=request.POST.get('line1'),
            line2=request.POST.get('line2'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            postal_code=request.POST.get('postal_code'),
            country=request.POST.get('country'),
            phone=request.POST.get('phone')  # <-- capture phone number
        )
    addresses = ShippingAddress.objects.filter(user=request.user)
    return render(request, "linetrendy/partials/address_list.html", {"addresses": addresses})




@login_required
def update_address(request):
    address_id = request.POST.get("address_id")
    if address_id:
        address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    else:
        address = ShippingAddress(user=request.user)

    address.full_name = request.POST.get("full_name")
    address.line1 = request.POST.get("line1")
    address.line2 = request.POST.get("line2")
    address.city = request.POST.get("city")
    address.state = request.POST.get("state")
    address.postal_code = request.POST.get("postal_code")
    address.country = request.POST.get("country")
    address.phone = request.POST.get("phone")
    address.save()

    addresses = ShippingAddress.objects.filter(user=request.user)
    return render(request, "linetrendy/partials/address_list.html", {"addresses": addresses})
    





@login_required
def delete_address(request):
    if request.method == "POST":
        address_id = request.POST.get("delete_address_id")
        ShippingAddress.objects.filter(id=address_id, user=request.user).delete()

        # After deletion, return the full tab content
        addresses = ShippingAddress.objects.filter(user=request.user)
        return render(request, "linetrendy/partials/address_list.html", {"addresses": addresses})







def order_tracking_view(request, order_number):
    """
    Track orders:
      - Logged-in users: their orders
      - Guests: their orders using session email
    """
    order_obj = None

    if request.user.is_authenticated:
        # User's own order
        order_obj = Order.objects.filter(order_number=order_number, user=request.user).first()
        if not order_obj:
            # Fallback to guest order if exists
            order_obj = Order.objects.filter(order_number=order_number, user=None).first()
    else:
        # Guest: require guest_email in session
        guest_email = request.session.get("guest_email")
        if guest_email:
            order_obj = Order.objects.filter(order_number=order_number, guest_email=guest_email).first()
        else:
            # Fallback if session lost (less secure but still works)
            order_obj = Order.objects.filter(order_number=order_number, user=None).first()

    if not order_obj:
        return HttpResponse("No order found with that number. Please check and try again.", status=404)

    # Steps definition
    steps = [
        {"label": "Order Placed", "status": "completed", "date": order_obj.created_at},
        {"label": "Shipped", "status": "pending"},
        {"label": "Out for Delivery", "status": "pending"},
        {"label": "Delivered", "status": "pending"},
    ]

    step_order = ["placed", "shipped", "out_for_delivery", "delivered"]
    current_index = step_order.index(order_obj.status) if order_obj.status in step_order else 0

    for i, step in enumerate(steps):
        if i < current_index:
            step["status"] = "completed"
        elif i == current_index:
            step["status"] = "current"
        else:
            step["status"] = "pending"

        step["color"] = (
            "bg-green-600" if step["status"] == "completed"
            else "bg-yellow-500 animate-pulse" if step["status"] == "current"
            else "bg-gray-400"
        )

    context = {
        "order": order_obj,
        "tracking_steps": steps,
        "current_step": current_index + 1,
        "total_steps": len(steps),
    }
    return render(request, "linetrendy/order_tracking.html", context)






@login_required
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Only allow cancel if status is "placed"
    if order.status == "placed":
        order.status = "cancelled"
        order.save()
        messages.success(request, f"Order {order.order_number} has been cancelled successfully.")
    else:
        messages.error(request, "This order cannot be cancelled.")

    return redirect("shop:account_page")







def guest_order_tracking(request):
    order = None
    order_number = request.GET.get("order_number")

    if order_number:
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            order = None

    # Define tracking steps (same as for authenticated users)
    tracking_steps = []
    if order:
        tracking_steps = [
            {"label": "Placed", "color": "bg-yellow-500" if order.status in ["placed", "shipped", "delivered"] else "bg-gray-300", "date": order.created_at},
            {"label": "Shipped", "color": "bg-blue-500" if order.status in ["shipped", "delivered"] else "bg-gray-300", "date": order.shipped_at if hasattr(order, "shipped_at") else None},
            {"label": "Delivered", "color": "bg-green-500" if order.status == "delivered" else "bg-gray-300", "date": order.delivered_at if hasattr(order, "delivered_at") else None},
        ]

    context = {
        "order": order,
        "tracking_steps": tracking_steps,
        "current_step": len([s for s in tracking_steps if "bg-" in s["color"] and s["color"] != "bg-gray-300"]),
        "total_steps": len(tracking_steps),
    }
    return render(request, "linetrendy/order_tracking.html", context)







def about(request):
    return render(request, 'linetrendy/about.html')


def contact(request):
    return render(request, 'linetrendy/contact.html')




def privacy_policy(request):
    return render(request, 'linetrendy/privacy_policy.html')


def term_of_service(request):
    return render(request, 'linetrendy/term_of_use.html')





def return_policy(request):
    return render(request, 'linetrendy/return_policy.html')




def faq(request):
    return render(request, 'linetrendy/faq.html')





def disclaimer(request):
    return render(request, 'linetrendy/disclaimer.html')






