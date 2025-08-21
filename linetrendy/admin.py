from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin

# Inline for product images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Number of empty image fields to show


# Category
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# Product
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'category', 'price', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]  # Allows adding images inline


# Product Image
@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ('product', 'image', 'created_at')
    search_fields = ('product__name',)





@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'product', 'quantity', 'created_at')
    search_fields = ('cart__user__username', 'product__name')  # <-- use related lookup
    list_filter = ('cart__user', 'product')  # <-- use related lookup

    def get_user(self, obj):
        return obj.cart.user
    get_user.short_description = 'User'




@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at', 'shipping_method', 'discount')
    search_fields = ('user__username', 'user__email')



# ShippingMethod
@admin.register(ShippingMethod)
class ShippingMethodAdmin(ModelAdmin):
    list_display = ('name', 'fee', 'free_over')
    search_fields = ('name',)


# Discount
@admin.register(Discount)
class DiscountAdmin(ModelAdmin):
    list_display = ('code', 'amount', 'percent', 'active')
    list_filter = ('active',)
    search_fields = ('code',)



