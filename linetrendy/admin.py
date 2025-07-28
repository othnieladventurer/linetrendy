from django.contrib import admin
from .models import *

# Register your models here.

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Number of empty image fields to show




@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)




@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]  # Allows adding images inline




@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'created_at')
    search_fields = ('product__name',)



    