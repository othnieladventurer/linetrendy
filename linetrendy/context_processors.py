from .cart import Cart
from .models import Category, CartItem
from django.db.models import Sum    



def cart_count(request):
    if request.user.is_authenticated:
        # Sum quantities of all CartItems whose cart belongs to this user
        count = CartItem.objects.filter(cart__user=request.user).aggregate(
            total_quantity=Sum('quantity')
        )['total_quantity'] or 0
    else:
        count = 0
    return {'cart_count': count}







def category_list(request):
    categories = Category.objects.all()
    return {'categories': categories}






