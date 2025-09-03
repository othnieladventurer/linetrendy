from .cart import Cart
from .models import Category, CartItem
from django.db.models import Sum    


def cart_count(request):
    if request.user.is_authenticated:
        # Existing working logic
        count = CartItem.objects.filter(cart__user=request.user).aggregate(
            total_quantity=Sum('quantity')
        )['total_quantity'] or 0
    else:
        # For guests, get cart via session
        from .utils import get_cart  # wherever your get_cart is defined
        cart = get_cart(request)
        count = cart.items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    return {'cart_count': count}





def category_list(request):
    categories = Category.objects.all()
    selected_category = request.GET.get('category')
    search_query = request.GET.get('q', '')

    try:
        selected_category = int(selected_category) if selected_category else None
    except (TypeError, ValueError):
        selected_category = None

    return {
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
    }






