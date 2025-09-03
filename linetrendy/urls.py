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

    #account page
    path('account-page/', views.account_page, name="account_page"),
    path('add-address/', views.add_address, name='add_address'),
     path('update-address/', views.update_address, name='update_address'),
    path('delete-address/', views.delete_address, name='delete_address'),
    path("track/<str:order_number>/", views.order_tracking_view, name="order_tracking"),
    path("cancel-order/<str:order_number>/", views.cancel_order, name="cancel_order"),
    path("track/", views.guest_order_tracking, name="guest_order_tracking"),


    #terms of use 
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.term_of_service, name='term_of_service'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('faq/', views.faq, name='faq'),


    

]





