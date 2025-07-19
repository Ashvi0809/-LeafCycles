from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, number, pincode, password=None):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), name=name, number=number, pincode=pincode)
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

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'number', 'pincode']

    def __str__(self):
        return self.email


class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
   # image = models.ImageField(upload_to='products/')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
   # uploaded_at = models.DateTimeField(auto_now_add=True)
  #  uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

