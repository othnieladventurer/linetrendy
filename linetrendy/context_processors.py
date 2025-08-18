from .cart import Cart
from .models import Category



def cart_count(request):
    return {'cart_count': Cart(request).count()}




def category_list(request):
    categories = Category.objects.all()
    return {'categories': categories}



