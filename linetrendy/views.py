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
    # Unauthenticated users → redirect to login with message
    if not request.user.is_authenticated:
        login_url = f"{reverse('users:account_login')}?next={request.get_full_path()}"
        messages.warning(request, "You need to sign in first to add items to the cart.")
        if request.headers.get("HX-Request") == "true":
            response = HttpResponse(status=401)
            response["HX-Redirect"] = login_url
            return response
        return redirect(login_url)

    # Authenticated POST → add item to cart
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        cart = Cart(request.user)
        cart.add(product_id=product.id, quantity=quantity)

        # HTMX request → update only the badge
        if request.headers.get("HX-Request") == "true":
            cart_count = cart.count()
            return render(request, "linetrendy/partials/cart_count.html", {"cart_count": cart_count})

        # fallback redirect
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Fallback for non-POST requests (prevent None return)
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



@login_required
def cart(request):
    return render(request, 'linetrendy/cart.html')





def about(request):
    return render(request, 'linetrendy/about.html')


def contact(request):
    return render(request, 'linetrendy/contact.html')




