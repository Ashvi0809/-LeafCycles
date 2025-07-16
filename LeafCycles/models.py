from django.db import models

class Plant(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
   # image = models.ImageField(upload_to='products/')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
   # uploaded_at = models.DateTimeField(auto_now_add=True)
  #  uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)