from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from django_countries.fields import CountryField
from django.db import transaction
import uuid

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to="categories",blank=True, null=True)
    slug = models.SlugField(unique=True, null=True, blank=True)  # ✅ add slug field

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    



    def __str__(self):
        return self.name




class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, null=True, blank=True, max_length=255)

    # ✅ Manually chosen related products
    related_products = models.ManyToManyField('self', blank=True, symmetrical=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:50]  # truncate to 50 chars
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                # leave room for "-1", "-2" etc
                slug = f"{base_slug[:45]}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_first_image(self):
        return self.images.first()

    def get_all_images(self):
        return self.images.all()

    def __str__(self):
        return self.name
    

    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"











class ShippingMethod(models.Model):
    name = models.CharField(max_length=100)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    free_over = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                    help_text="Subtotal amount over which shipping is free")

    def get_fee(self, subtotal):
        """Return fee based on subtotal and free_over threshold"""
        if self.free_over and subtotal >= self.free_over:
            return Decimal('0.00')
        return self.fee

    def __str__(self):
        return self.name





class Discount(models.Model):
    code = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                  help_text="Percentage discount, e.g., 10 for 10%")
    active = models.BooleanField(default=True)

    def get_discount(self, subtotal):
        """Calculate discount amount based on subtotal"""
        if self.amount:
            return self.amount
        elif self.percent:
            return subtotal * (self.percent / 100)
        return Decimal('0.00')

    def __str__(self):
        return self.code
    





class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    shipping_method = models.ForeignKey('ShippingMethod', null=True, blank=True, on_delete=models.SET_NULL)
    discount = models.ForeignKey('Discount', null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.email}"
        return f"Guest Cart {self.session_key}"

        





class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE,related_name="items", null=True, blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"






class Order(models.Model):
    STATUS_CHOICES = [
        ("placed", "Order Placed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)
    payment_intent_id = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="placed"
    )

    order_number = models.CharField(max_length=30, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            today = timezone.now().strftime("%Y%m%d")
            with transaction.atomic():
                last_order = (
                    Order.objects.filter(order_number__startswith=f"ORD{today}")
                    .order_by("-order_number")
                    .first()
                )
                if last_order:
                    last_seq = int(last_order.order_number.split("-")[-1])
                    new_seq = last_seq + 1
                else:
                    new_seq = 1
                self.order_number = f"ORD{today}-{new_seq:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        display_status = dict(self.STATUS_CHOICES).get(self.status, self.status)
        if self.user:
            return f"Order {self.order_number} by {self.user.email} - {display_status} (${self.total_amount})"
        elif self.guest_email:
            return f"Order {self.order_number} by Guest ({self.guest_email}) - {display_status} (${self.total_amount})"
        else:
            return f"Order {self.order_number} by Guest #{self.id} - {display_status} (${self.total_amount})"











class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)  # ✅ new field
    product_name = models.CharField(max_length=255)  # keep for snapshot history
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} × {self.product_name} (${self.price})"
    





class BillingAddress(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='billing_address')
    full_name = models.CharField(max_length=255)
    line1 = models.CharField("Street Address", max_length=255)
    line2 = models.CharField("Apartment/Suite (Optional)", max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = CountryField(default='US')

    def __str__(self):
        return f"{self.full_name}, {self.line1}, {self.city}"




 

class ShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        null=True,
        blank=True
    )
    order = models.OneToOneField(
        'Order',
        on_delete=models.SET_NULL,
        related_name='shipping_address',
        null=True,
        blank=True
    )
    full_name = models.CharField(max_length=255)
    line1 = models.CharField("Street Address", max_length=255)
    line2 = models.CharField("Apartment/Suite (Optional)", max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = CountryField(default='US')
    phone = models.CharField(max_length=20, blank=True, null=True) 

    def __str__(self):
        return f"{self.full_name}, {self.line1}, {self.city}"
















