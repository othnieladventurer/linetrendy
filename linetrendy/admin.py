from django.contrib import admin
from unfold.admin import ModelAdmin  # Use django-unfold
from .models import *
from .forms import TestimonialAdminForm
from django.utils.html import format_html   

# ----------------------
# Product & Category
# ----------------------


admin.site.site_header = "Linetrendy Admin"
admin.site.site_title = "Linetrendy Admin Portal"
admin.site.index_title = "Welcome to Linetrendy Dashboard"




class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Number of empty image fields to show




@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)




@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("name", "category", "price", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("name", "description")
    inlines = [ProductImageInline]




@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ("product", "image", "created_at")
    search_fields = ("product__name",)

# ----------------------
# Cart
# ----------------------

@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):
    list_display = ("get_user", "product", "quantity", "created_at")
    search_fields = ("cart__user__email", "product__name")
    list_filter = ("product",)

    def get_user(self, obj):
        return obj.cart.user.email if obj.cart.user else "Guest"
    get_user.short_description = "User"




@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("user", "updated_at", "shipping_method", "discount")
    search_fields = ("user__email", "user__username")

# ----------------------
# Shipping & Billing
# ----------------------

@admin.register(ShippingMethod)
class ShippingMethodAdmin(ModelAdmin):
    list_display = ("name", "fee", "free_over")
    search_fields = ("name",)




@admin.register(Discount)
class DiscountAdmin(ModelAdmin):
    list_display = ("code", "amount", "percent", "active")
    list_filter = ("active",)
    search_fields = ("code",)




@admin.register(DiscountUsage)
class DiscountUsageAdmin(ModelAdmin):
    list_display = ("user", "discount", "used_at")
    list_filter = ("used_at",)
    search_fields = ("user__username", "discount__code")


    


@admin.register(BillingAddress)
class BillingAddressAdmin(ModelAdmin):
    list_display = ("order", "full_name", "city", "state", "country")
    search_fields = ("full_name", "city", "state", "postal_code", "country")



@admin.register(ShippingAddress)
class ShippingAddressAdmin(ModelAdmin):
    list_display = ("order", "full_name", "city", "state", "country")
    search_fields = ("full_name", "city", "state", "postal_code", "country")

# ----------------------
# Orders
# ----------------------

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
class OrderItemAdmin(ModelAdmin):
    list_display = ("id", "order_number", "customer_display", "product", "product_name", "quantity", "price")
    search_fields = ("product_name", "order__order_number", "order__user__email", "order__guest_email")
    list_filter = ("order__status",)
    readonly_fields = ("product_name", "quantity", "price")  # snapshot fields read-only

    fieldsets = (
        ("Order Info", {"fields": ("order",)}),
        ("Product Info", {"fields": ("product", "product_name")}),
        ("Quantity & Price", {"fields": ("quantity", "price")}),
    )

    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = "Order #"
    order_number.admin_order_field = "order__order_number"

    def customer_display(self, obj):
        if obj.order.user:
            return obj.order.user.email
        elif obj.order.guest_email:
            return f"Guest ({obj.order.guest_email})"
        return f"Guest #{obj.order.id}"
    customer_display.short_description = "Customer"







@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("email", "subscribed_at", "is_active")
    list_filter = ("is_active", "subscribed_at")
    search_fields = ("email",)
    ordering = ("-subscribed_at",)









@admin.register(Testimonial)
class TestimonialAdmin(ModelAdmin):
    form = TestimonialAdminForm

    list_display = ("name", "short_content", "created_at", "preview_image", "rating_stars")
    readonly_fields = ("created_at", "preview_image", "rating_stars")  # preview only
    search_fields = ("name", "content")
    ordering = ("-created_at",)

    # Include rating in the form
    fieldsets = (
        ("Client Info", {
            "fields": ("name", "image", "rating"),  # rating editable here
        }),
        ("Testimonial Content", {
            "fields": ("content",),
        }),
        ("Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    # Short preview of content
    def short_content(self, obj):
        return (obj.content[:60] + "...") if len(obj.content) > 60 else obj.content
    short_content.short_description = "Content Preview"

    # Image preview
    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;" />', obj.image.url)
        return "—"
    preview_image.short_description = "Image"

    # Dynamic star preview
    def rating_stars(self, obj):
        html = '<div class="flex space-x-1">'
        for i in range(1, 6):
            if i <= obj.rating:
                html += '<i class="fas fa-star text-blue-600"></i>'
            else:
                html += '<i class="fas fa-star text-gray-300"></i>'
        html += '</div>'
        return format_html(html)
    rating_stars.short_description = "Rating"

    