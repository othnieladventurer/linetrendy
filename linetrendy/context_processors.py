from .cart import Cart
from .models import Category

def cart_count(request):
    if request.user.is_authenticated:
        count = Cart(request.user).count()  # pass request.user, not request
    else:
        count = 0  # or None, if you prefer
    return {'cart_count': count}







def category_list(request):
    categories = Category.objects.all()
    return {'categories': categories}






