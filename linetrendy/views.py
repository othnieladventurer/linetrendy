from django.shortcuts import render, get_object_or_404
from .models import *

# Create your views here.





def index(request):
    product=Product.objects.all().order_by('-created_at')

    context = {
        'products': product[:8],  
    }
    return render(request, 'linetrendy/index.html', context)



def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    context = {
        'product': product,
  
    }
    return render(request, 'linetrendy/product_detail.html', context)





def shop(request):
    return render(request, 'linetrendy/shop.html')



def about(request):
    return render(request, 'linetrendy/about.html')


def contact(request):
    return render(request, 'linetrendy/contact.html')




