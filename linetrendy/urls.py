from django.urls import path
from . import views





app_name = 'shop'


urlpatterns = [
    path('', views.index, name="index" ),
    path('shop/', views.shop, name="shop" ),
    path('detail/<slug:slug>/', views.product_detail, name="product_detail"),
    path('about/', views.about, name="about" ),
    path('contact/', views.contact, name="contact" ),

]





