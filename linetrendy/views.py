import stripe
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
import json
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY







def index(request):
    product=Product.objects.all().order_by('-created_at')
    category = Category.objects.all()

    context = {
        'products': product[:8],
        'categories': category,  
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
    # Get or create cart for this user (guest or authenticated)
    cart = get_cart(request)
    cart_items = cart.items.select_related('product').all()

    # Compute cart count
    cart_count = sum(item.quantity for item in cart_items)

    # Handle shipping selection or promo code
    if request.method == 'POST':
        if request.headers.get("HX-Request"):  # HTMX request
            # Shipping
            if 'shipping_method' in request.POST:
                method_id = request.POST.get('shipping_method')
                cart.shipping_method = get_object_or_404(ShippingMethod, id=method_id)
                cart.save()

            # Promo code
            if 'promo_code' in request.POST:
                code = request.POST.get('promo_code')
                try:
                    discount_obj = Discount.objects.get(code__iexact=code, active=True)
                    cart.discount = discount_obj
                    cart.save()
                except Discount.DoesNotExist:
                    cart.discount = None
                    cart.save()

            # Compute totals
            subtotal = sum(item.product.price * item.quantity for item in cart_items)

            # Determine if shipping is required
            require_shipping_address = subtotal <= 35

            shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method and require_shipping_address else Decimal('0.00')
            discount = cart.discount.get_discount(subtotal) if cart.discount and cart.discount.active else Decimal('0.00')
            final_total = max(subtotal + shipping_fee - discount, Decimal('0.00'))

            context = {
                'cart_items': cart_items,
                'cart': cart,
                'cart_count': cart_count,
                'total_price': subtotal,
                'shipping_fee': shipping_fee,
                'discount': discount,
                'final_total': final_total,
                'shipping_methods': ShippingMethod.objects.all(),
                'require_shipping_address': require_shipping_address,
            }
            return render(request, 'linetrendy/partials/cart_totals.html', context)

        else:
            # Regular POST fallback for non-HTMX
            if 'shipping_method' in request.POST:
                method_id = request.POST.get('shipping_method')
                cart.shipping_method = get_object_or_404(ShippingMethod, id=method_id)
                cart.save()

            if 'promo_code' in request.POST:
                code = request.POST.get('promo_code')
                try:
                    discount_obj = Discount.objects.get(code__iexact=code, active=True)
                    cart.discount = discount_obj
                    cart.save()
                except Discount.DoesNotExist:
                    cart.discount = None
                    cart.save()
            return redirect('shop:cart')

    # Normal GET request
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    require_shipping_address = subtotal <= 35
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method and require_shipping_address else Decimal('0.00')
    discount = cart.discount.get_discount(subtotal) if cart.discount and cart.discount.active else Decimal('0.00')
    final_total = max(subtotal + shipping_fee - discount, Decimal('0.00'))

    context = {
        'cart_items': cart_items,
        'cart': cart,
        'cart_count': cart_count,
        'total_price': subtotal,
        'shipping_fee': shipping_fee,
        'discount': discount,
        'final_total': final_total,
        'shipping_methods': ShippingMethod.objects.all(),
        'require_shipping_address': require_shipping_address,
    }

    return render(request, 'linetrendy/cart.html', context)





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
    require_shipping_address = subtotal <= Decimal("35.00")

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
        "cart_count": cart_count
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "linetrendy/partials/cart_updated_htmx.html", context)

    return redirect("shop:cart")





def checkout(request):
    cart = get_cart(request)
    cart_items = cart.items.select_related('product').all()

    if not cart_items:
        return redirect("shop:cart")

    subtotal = sum((item.product.price if item.product else 0) * item.quantity for item in cart_items)
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else Decimal("0.00")
    discount = cart.discount.get_discount(subtotal) if cart.discount and cart.discount.active else Decimal("0.00")
    final_total = max(subtotal + shipping_fee - discount, Decimal("0.00"))

    stripe.api_key = settings.STRIPE_SECRET_KEY
    intent = stripe.PaymentIntent.create(
        amount=int(final_total * 100),
        currency="usd",
        automatic_payment_methods={"enabled": True},
    )

    if request.method == "POST":
        payment_intent_id = intent.id
        selected_address_id = request.POST.get("shipping_address")

        # --- Order Creation ---
        if request.user.is_authenticated:
            order = Order.objects.create(
                user=request.user,
                cart=cart,
                total_amount=final_total,
                payment_intent_id=payment_intent_id,
            )

            # Use existing address if selected
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

            # Prepare email for authenticated user
            tracking_url = request.build_absolute_uri(
                reverse('shop:order_tracking', args=[order.order_number])
            )
            email_subject = f"Order Confirmation - {order.order_number}"
            email_message = (
                f"Hi {request.user.first_name},\n\n"
                f"Thank you for your order! Your order number is {order.order_number}.\n"
                f"You can track your order here: {tracking_url}\n\n"
                "Best regards,\nLinetrendy Team"
            )
            email_to = request.user.email

        else:  # Guest user
            guest_email = request.POST.get("email")
            if not guest_email:
                return HttpResponse("Guest email is required", status=400)

            order = Order.objects.create(
                guest_email=guest_email,
                cart=cart,
                total_amount=final_total,
                payment_intent_id=payment_intent_id,
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

            # Prepare email for guest user
            guest_tracking_url = request.build_absolute_uri(
                f"{reverse('shop:guest_order_tracking')}?order_number={order.order_number}"
            )
            email_subject = f"Order Confirmation - {order.order_number}"
            email_message = (
                f"Hi,\n\n"
                f"Thank you for your order! Your order number is {order.order_number}.\n"
                f"You can track your order here: {guest_tracking_url}\n\n"
                "Best regards,\nYour Shop Team"
            )
            email_to = guest_email

        # --- Create Order Items ---
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product if item.product else None,
                product_name=item.product.name if item.product else getattr(item, 'product_name', "Unknown Product"),
                quantity=item.quantity,
                price=item.product.price if item.product else getattr(item, 'price', 0),
            )

        # --- Clear Cart ---
        cart.items.all().delete()
        cart.shipping_method = None
        cart.discount = None
        cart.save()

        # --- Send Confirmation Email ---
        try:
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_to],
                fail_silently=False,
            )
        except Exception as e:
            # Log the error instead of crashing
            logger.error(f"Failed to send order email for order {order.order_number}: {e}")

        # --- Save payment intent in session ---
        request.session["last_payment_intent_id"] = payment_intent_id

        return redirect("shop:checkout_success")

    # --- Context for GET request ---
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














def checkout_success(request):
    last_order_intent = request.session.get("last_payment_intent_id")
    if not last_order_intent:
        return HttpResponse("No recent order found.", status=400)

    # Get the order linked to this payment_intent
    try:
        if request.user.is_authenticated:
            order = Order.objects.get(user=request.user, payment_intent_id=last_order_intent)
        else:
            guest_email = request.session.get("guest_email")
            order = Order.objects.get(guest_email=guest_email, payment_intent_id=last_order_intent)
    except Order.DoesNotExist:
        return HttpResponse("Order not found.", status=404)

    # Calculate totals from order items
    order_items = order.items.select_related('product').all()
    subtotal = sum(item.price * item.quantity for item in order_items)
    shipping_fee = order.cart.shipping_method.get_fee(subtotal) if order.cart and order.cart.shipping_method else Decimal("0.00")
    discount = order.cart.discount.get_discount(subtotal) if order.cart and order.cart.discount and order.cart.discount.active else Decimal("0.00")
    final_total = max(subtotal + shipping_fee - discount, Decimal("0.00"))

    # --- Prepare tracking URLs ---
    if request.user.is_authenticated:
        tracking_url = request.build_absolute_uri(
            reverse('shop:order_tracking', args=[order.order_number])
        )
    else:
        # Use query parameter for guest
        tracking_url = request.build_absolute_uri(
            f"{reverse('shop:guest_order_tracking')}?order_number={order.order_number}"
        )

    # Clear session
    request.session.pop("last_payment_intent_id", None)
    request.session.pop("guest_email", None)

    context = {
        "order": order,
        "order_items": order_items,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "discount": discount,
        "final_total": final_total,
        "tracking_url": tracking_url,  # Pass tracking URL to template
    }
    return render(request, "linetrendy/checkout_success.html", context)


@csrf_exempt
def store_payment_intent(request):
    if request.method == "POST":
        data = json.loads(request.body)
        request.session["last_payment_intent_id"] = data.get("payment_intent_id")
        # also store guest email if present
        if "guest_email" in data:
            request.session["guest_email"] = data["guest_email"]
        return HttpResponse("OK")
    return HttpResponse("Method not allowed", status=405)



    






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
    Allow:
      - Logged-in users: track only their own orders
      - Guests: track order by order_number only
    """
    if request.user.is_authenticated:
        # Logged-in user: must belong to them
        order_obj = get_object_or_404(Order, order_number=order_number, user=request.user)
    else:
        # Guest: allow lookup only by order_number
        order_obj = get_object_or_404(Order, order_number=order_number)

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







