from django.urls import path
from . import views





app_name = 'shop'


urlpatterns = [
    path('', views.index, name="index" ),
    path('shop/', views.shop, name="shop" ),
    path('cart/', views.cart, name="cart" ),
    path('detail/<slug:slug>/', views.product_detail, name="product_detail"),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update-quantity/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('store-payment-intent/', views.store_payment_intent, name='store_payment_intent'),
    path('about/', views.about, name="about" ),
    path('contact/', views.contact, name="contact" ),
    

]





