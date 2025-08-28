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





@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("order_number", "customer_display", "total_amount", "status", "created_at")
    readonly_fields = ("order_number",)
    search_fields = ("user__email", "guest_email", "order_number")
    list_filter = ("status", "created_at")

    def customer_display(self, obj):
        if obj.user:
            return obj.user.email
        elif obj.guest_email:
            return f"Guest ({obj.guest_email})"
        return f"Guest #{obj.id}"
    customer_display.short_description = "Customer"





@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'quantity', 'price')
    search_fields = ('product_name', 'order__id')





@admin.register(BillingAddress)
class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ("order", "full_name", "city", "state", "country")
    search_fields = ("full_name", "city", "state", "postal_code", "country")



@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ("order", "full_name", "city", "state", "country")
    search_fields = ("full_name", "city", "state", "postal_code", "country")











