from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser  # adjust this import if your model file name is different
from .models import Product
from .models import Category
from .models import WishlistItem, CartItem
from .models import Review
from .models import ContactMessage



class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('email', 'name', 'number', 'pincode', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'name', 'number', 'pincode', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'number', 'pincode', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'uploaded_at', 'uploaded_by')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'comment', 'created_at')


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at')
    search_fields = ('name', 'email', 'subject', 'message')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(WishlistItem)
admin.site.register(CartItem)
admin.site.register(Review, ReviewAdmin)
admin.site.register(ContactMessage)