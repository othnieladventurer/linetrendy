from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import *
from .cart import Cart
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from datetime import date
# Create your views here.







#Add to cart

@login_required
def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        cart = Cart(request.user)
        cart.add(product_id=product.id, quantity=quantity)

        # If it's an HTMX request, return partial update
        if request.headers.get("HX-Request") == "true":
            cart_count = cart.count()  # make sure you have this method
            return render(request, "linetrendy/partials/cart_count.html", {"cart_count": cart_count})

        # fallback redirect
        return redirect(request.META.get('HTTP_REFERER', '/'))






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




