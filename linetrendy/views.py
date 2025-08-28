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
    product=Product.objects.all().order_by('-created_at')
    category = Category.objects.all()

    context = {
        'products': product[:8],
        'categories': category,  
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
            shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else Decimal('0.00')
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
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else Decimal('0.00')
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
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else 0
    discount = cart.discount.get_discount(subtotal) if cart.discount and cart.discount.active else 0
    final_total = max(subtotal + shipping_fee - discount, 0)
    cart_count = sum(i.quantity for i in cart_items)

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
        return redirect("shop:cart")  # No items, redirect to cart

    # Calculate totals
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else 0
    discount = cart.discount.get_discount(subtotal) if cart.discount and cart.discount.active else 0
    final_total = max(subtotal + shipping_fee - discount, 0)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(final_total * 100),  # Stripe expects cents
            currency="usd",
            automatic_payment_methods={"enabled": True},
        )
        print("Created PaymentIntent:", intent.id, intent.status, intent.amount)
    except Exception as e:
        print("Stripe PaymentIntent error:", str(e))
        return HttpResponse("Error creating payment intent. Check server logs.", status=500)

    # Handle POST for creating order
    if request.method == "POST":
        payment_intent_id = intent.id
        if request.user.is_authenticated:
            order = Order.objects.create(
                user=request.user,
                cart=cart,
                total_amount=final_total,
                payment_intent_id=payment_intent_id
            )
        else:
            guest_email = request.POST.get("email")
            if not guest_email:
                return HttpResponse("Guest email is required", status=400)
            order = Order.objects.create(
                guest_email=guest_email,
                cart=cart,
                total_amount=final_total,
                payment_intent_id=payment_intent_id
            )

        # Copy cart items to order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_name=item.product.name,
                quantity=item.quantity,
                price=item.product.price
            )

        # Clear cart after order
        cart.items.all().delete()

        return redirect("order_success_page")  # Replace with your success URL

    context = {
        "cart": cart,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "discount": discount,
        "final_total": final_total,
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
        "client_secret": intent.client_secret,
    }

    return render(request, "linetrendy/checkout.html", context)





def checkout_success(request):
    # Get last payment intent
    last_order_intent = request.session.get("last_payment_intent_id")
    if not last_order_intent:
        return HttpResponse("No recent order found.", status=400)

    # Get cart and items
    cart = get_cart(request)
    cart_items = list(cart.items.select_related('product').all())
    if not cart_items:
        return HttpResponse("Cart is empty.", status=400)

    # Calculate totals
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else Decimal("0.00")
    discount = cart.discount.get_discount(subtotal) if cart.discount and cart.discount.active else Decimal("0.00")
    final_total = max(subtotal + shipping_fee - discount, Decimal("0.00"))

    # Prepare order fields
    order_data = {
        "cart": cart,
        "payment_intent_id": last_order_intent,
        "total_amount": final_total,
        # Status will default to "placed"
    }

    if request.user.is_authenticated:
        order_data["user"] = request.user
    else:
        order_data["guest_email"] = request.session.get("guest_email")

    # Create the order
    order = Order.objects.create(**order_data)

    # Create order items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            quantity=item.quantity,
            price=item.product.price,
        )

    # Clear the cart
    cart.items.all().delete()
    cart.shipping_method = None
    cart.discount = None
    cart.save()

    # Clear session variables
    request.session.pop("last_payment_intent_id", None)
    request.session.pop("guest_email", None)

    # Render confirmation
    context = {
        "order": order,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "discount": discount,
        "final_total": final_total,
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



    

def about(request):
    return render(request, 'linetrendy/about.html')


def contact(request):
    return render(request, 'linetrendy/contact.html')






@login_required
def account_page(request):
    # Fetch orders for the logged-in user
    orders = Order.objects.filter(user=request.user).order_by('-created_at')


    # Paginate: 10 orders per page
    paginator = Paginator(orders, 10)  # 10 orders per page
    page_number = request.GET.get('page')   # Get page number from query params
    orders = paginator.get_page(page_number)  # This returns a Page object

    context = {
        'orders': orders,
    }
    return render(request, 'linetrendy/account_page.html', context)








