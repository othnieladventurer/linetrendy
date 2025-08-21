from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from .models import *
from .models import Cart, CartItem, Discount, ShippingMethod
from django.urls import reverse  
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string

# Create your views here.









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




@login_required
def cart(request):
    # Get or create cart for this user
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product')

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
        'total_price': subtotal,
        'shipping_fee': shipping_fee,
        'discount': discount,
        'final_total': final_total,
        'shipping_methods': ShippingMethod.objects.all(),
    }

    return render(request, 'linetrendy/cart.html', context)





#Add to cart
@login_required
def cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Handle shipping selection
    if request.method == 'POST' and 'shipping_method' in request.POST:
        method_id = request.POST.get('shipping_method')
        cart.shipping_method = get_object_or_404(ShippingMethod, id=method_id)
        cart.save()

    # Handle promo code
    if request.method == 'POST' and 'promo_code' in request.POST:
        code = request.POST.get('promo_code')
        try:
            discount_obj = Discount.objects.get(code__iexact=code, active=True)
            cart.discount = discount_obj
            cart.save()
        except Discount.DoesNotExist:
            cart.discount = None
            cart.save()

    cart_items = cart.items.select_related('product')
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else 0
    discount = cart.discount.get_discount(subtotal) if cart.discount and cart.discount.active else 0
    final_total = max(subtotal + shipping_fee - discount, 0)

    context = {
        'cart_items': cart_items,
        'total_price': subtotal,
        'shipping_fee': shipping_fee,
        'discount': discount,
        'final_total': final_total,
        'cart': cart,
        'shipping_methods': ShippingMethod.objects.all(),
    }

    if request.headers.get('Hx-Request') == 'true':
        # Return only the fragment for HTMX
        html = render_to_string('linetrendy/partials/cart_totals.html', context, request=request)
        return HttpResponse(html)
    
    # Full page render
    return render(request, 'linetrendy/cart.html', context)





def add_to_cart(request):
    if not request.user.is_authenticated:
        login_url = f"{reverse('users:account_login')}?next={request.get_full_path()}"
        messages.warning(request, "You need to sign in first to add items to the cart.")
        if request.headers.get("HX-Request") == "true":
            response = HttpResponse(status=401)
            response["HX-Redirect"] = login_url
            return response
        return redirect(login_url)

    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        cart, _ = Cart.objects.get_or_create(user=request.user)
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






@login_required
def update_cart_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')

    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        cart_item.quantity = max(1, cart_item.quantity - 1)

    cart_item.save()
    cart_items = cart_item.cart.items.select_related('product').all()
    cart = cart_item.cart

    subtotal = sum(i.product.price * i.quantity for i in cart_items)
    shipping_fee = cart.shipping_method.get_fee(subtotal) if cart.shipping_method else 0
    discount = cart.discount.get_discount(subtotal) if cart.discount and cart.discount.active else 0
    final_total = max(subtotal + shipping_fee - discount, 0)
    cart_count = sum(i.quantity for i in cart_items)
    shipping_methods = ShippingMethod.objects.all()

    context = {
        "cart_items": cart_items,
        "cart": cart,
        "total_price": subtotal,
        "shipping_fee": shipping_fee,
        "discount": discount,
        "final_total": final_total,
        "cart_count": cart_count,
        "shipping_methods": shipping_methods,
    }

    html = render_to_string("linetrendy/partials/cart_updated_htmx.html", context, request=request)
    return HttpResponse(html)






def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    
    cart = request.user.cart
    cart_items = cart.items.all()
    total_price = sum(i.product.price * i.quantity for i in cart_items)
    shipping_fee = cart.shipping_method.fee if cart.shipping_method else 0
    discount = cart.discount_amount if hasattr(cart, 'discount_amount') else 0
    final_total = total_price + shipping_fee - discount
    cart_count = cart_items.count()  # update cart count

    if request.headers.get("HX-Request"):
        context = {
            "cart": cart,
            "cart_items": cart_items,
            "total_price": total_price,
            "shipping_fee": shipping_fee,
            "discount": discount,
            "final_total": final_total,
            "cart_count": cart_count
        }
        return render(request, "linetrendy/partials/cart_updated_htmx.html", context)

    return redirect("shop:cart")










@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'linetrendy/checkout.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
    })


def about(request):
    return render(request, 'linetrendy/about.html')


def contact(request):
    return render(request, 'linetrendy/contact.html')




