from django.urls import path
from . import views





app_name = 'shop'


urlpatterns = [
    path('', views.index, name="index" ),
    path('shop/', views.shop, name="shop" ),
    path('cart/', views.cart, name="cart" ),
    path('detail/<slug:slug>/', views.product_detail, name="product_detail"),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('about/', views.about, name="about" ),
    path('contact/', views.contact, name="contact" ),
    

]





