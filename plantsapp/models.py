from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, number, pincode, password=None):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), name=name, number=number, pincode=pincode, date_joined=timezone.now())
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, number, pincode, password):
        user = self.create_user(email, name, number, pincode, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=15)
    pincode = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'number', 'pincode']

    def __str__(self):
        return self.email

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    origin = models.CharField(max_length=100, blank=True, null=True)
    material = models.CharField(max_length=255, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    certification_name = models.CharField(max_length=255, blank=True, null=True)
    shelf_life = models.CharField(max_length=100, blank=True, null=True)
    storage = models.TextField(blank=True, null=True)
    features = models.JSONField(default=list, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_products'
    )

    @property
    def avg_rating(self):
        return self.reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.product.name} by {self.buyer.email}"

class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} - {self.product.name}"

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.rating}★)"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"