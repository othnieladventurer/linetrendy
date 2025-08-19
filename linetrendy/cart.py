# shop/cart.py
from .models import CartItem, Product
from django.db.models import Sum

class Cart:
    def __init__(self, user):
        if not user.is_authenticated:
            raise ValueError("User must be logged in to use the cart.")
        self.user = user

    def add(self, product_id, quantity=1):
        product = Product.objects.get(id=product_id)
        cart_item, created = CartItem.objects.get_or_create(
            user=self.user,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

    def count(self):
        """Return total quantity of items in user's cart"""
        return CartItem.objects.filter(user=self.user).aggregate(
            total=Sum('quantity')
        )['total'] or 0






