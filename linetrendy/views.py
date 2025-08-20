from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from .models import *
from .cart import Cart
from django.urls import reverse  
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Create your views here.






#Add to cart
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

        cart = Cart(request.user)
        cart.add(product_id=product.id, quantity=quantity)

        # HTMX request → return button updated to "Added"
        if request.headers.get("HX-Request") == "true":
            cart_count = cart.count()
            return render(
                request,
                "linetrendy/partials/cart_button_added.html",
                {"product": product, "cart_count": cart_count}
            )

        return redirect(request.META.get("HTTP_REFERER", "/"))

    return redirect("/")






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




from decimal import Decimal
@login_required
def cart(request):
    # Get all cart items for the logged-in user
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')

    # Calculate subtotal
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Shipping logic
    shipping_fee = Decimal('10.00') if total_price > 0 else Decimal('0.00')

    # Discount logic (update if promo code applied)
    discount = Decimal('0.00')

    # Calculate final total
    final_total = total_price + shipping_fee - discount

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_fee': shipping_fee,
        'discount': discount,
        'final_total': final_total,  # pass final total
    }

    return render(request, 'linetrendy/cart.html', context)






@login_required
def update_cart_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    action = request.POST.get('action')

    if action == 'increase':
        item.quantity += 1
    elif action == 'decrease' and item.quantity > 1:
        item.quantity -= 1

    item.save()
    return redirect('shop:cart')



@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('shop:cart')



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




