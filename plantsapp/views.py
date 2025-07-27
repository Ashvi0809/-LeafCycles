from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from .serializers import RegisterSerializer, LoginSerializer
from .models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import Product
from django.shortcuts import get_object_or_404
from .models import WishlistItem
from .forms import ProductForm
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import CartItem
from django.db.models import Count
from django.views.decorators.http import require_POST
from .models import ContactMessage
from .models import Category
from .models import Product
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.views.decorators.csrf import csrf_protect


otp_storage = {}

# -------------------------
# Web Form Views (HTML)
# -------------------------

def signup_form(request):
    if request.method == "POST":
        data = {
            "email": request.POST.get("email"),
            "name": request.POST.get("name"),
            "number": request.POST.get("number"),
            "pincode": request.POST.get("pincode"),
            "password": request.POST.get("password"),
            "confirm_password": request.POST.get("confirm_password"),
        }
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return redirect("/api/login-form/")
        else:
            return render(request, "plantsapp/signup.html", {"errors": serializer.errors})
    return render(request, "plantsapp/signup.html")

def login_form(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(email=email, password=password)
        if user is not None:
            return redirect("/api/home/")
        else:
            return render(request, "plantsapp/login.html", {"error": "Invalid email or password"})
    return render(request, "plantsapp/login.html")

def home_view(request):
    return render(request, "plantsapp/home.html")

def forgot_password_form(request):
    return render(request, 'plantsapp/forgot_password.html')

def verify_otp_form(request):
    return render(request, 'plantsapp/verify_otp.html')

def reset_password_form(request):
    return render(request, 'plantsapp/reset_password.html')


# -------------------------
# API Views (DRF)
# -------------------------

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    queryset = CustomUser.objects.all()

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            code = str(random.randint(100000, 999999))
            otp_storage[email] = code
            send_mail(
                "Password Reset Code",
                f"Your OTP code is: {code}",
                settings.EMAIL_HOST_USER,
                [email]
            )
            return Response({"msg": "OTP sent to email"})
        return Response({"error": "User not found"}, status=404)

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        if otp_storage.get(email) == code:
            return Response({"msg": "OTP verified"})
        return Response({"error": "Invalid OTP"}, status=400)

class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")
        if password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)
        user = CustomUser.objects.filter(email=email).first()
        if user:
            user.set_password(password)
            user.save()
            return Response({"msg": "Password reset successful"})
        return Response({"error": "User not found"}, status=404)

def product_list(request):
    products = Product.objects.annotate(review_count=Count('reviews'))
    categories = Category.objects.all()
    wishlist_ids = []

    if request.user.is_authenticated:
        wishlist_ids = WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True)

    return render(request, 'plantsapp/product_list.html', {
        'products': products,
        'wishlist_ids': list(wishlist_ids),
        'categories': categories,
        'selected_category': None
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    in_wishlist = False

    if request.user.is_authenticated:
        in_wishlist = WishlistItem.objects.filter(user=request.user, product=product).exists()

    return render(request, 'plantsapp/product_detail.html', {
        'product': product,
        'in_wishlist': in_wishlist
    })



@login_required
@csrf_protect
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        category = Category.objects.get(id=category_id)
        image = request.FILES.get('image')
        description = request.POST.get('description')
        price = request.POST.get('price')

        # Additional form fields
        origin = request.POST.get('origin')
        material = request.POST.get('material')
        dimensions = request.POST.get('dimensions')
        weight = request.POST.get('weight')
        certification_name = request.POST.get('certification_name')
        shelf_life = request.POST.get('shelf_life')
        storage = request.POST.get('storage')

        # Gather dynamic features
        features = []
        for key in request.POST:
            if key.startswith('feature_'):
                feature_value = request.POST.get(key)
                if feature_value:
                    features.append(feature_value)

        # Save product to DB
        product = Product.objects.create(
            name=name,
            category=category,
            image=image,
            description=description,
            price=price,
            origin=origin,
            material=material,
            dimensions=dimensions,
            weight=weight,
            certification_name=certification_name,
            shelf_life=shelf_life,
            storage=storage,
            features=features,
            uploaded_by=request.user
        )

        return redirect('product_list')

    categories = Category.objects.all()
    return render(request, 'plantsapp/add_product.html', {'categories': categories})


@csrf_exempt
def toggle_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)

        # You can use a fixed dummy user for now if no auth:
        user = request.user if request.user.is_authenticated else None

        if not user:
            return JsonResponse({'error': 'User not authenticated'}, status=403)

        wishlist_item, created = WishlistItem.objects.get_or_create(user=user, product=product)

        if not created:
            wishlist_item.delete()
            return JsonResponse({'status': 'removed'})
        else:
            return JsonResponse({'status': 'added'})

    return JsonResponse({'error': 'Invalid request'}, status=400)
@login_required
def wishlist_view(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user)
    return render(request, 'plantsapp/wishlist.html', {'wishlist_items': wishlist_items})

@csrf_exempt
def add_to_cart(request, product_id):
    if request.method == 'POST' and request.user.is_authenticated:
        product = Product.objects.get(id=product_id)
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        return JsonResponse({'status': 'added'})
    return JsonResponse({'status': 'unauthorized'}, status=403)


@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'plantsapp/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })
def landing_page(request):
    return render(request, 'plantsapp/landing.html')

@require_POST
@login_required
def rate_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    rating = int(request.POST.get("rating"))
    user = request.user

    review, created = Review.objects.get_or_create(user=user, product=product)
    review.rating = rating
    review.save()

    return redirect("product_list")  # or use `request.META.get('HTTP_REFERER')`

def home_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        # Optional: success message or redirect
        return redirect('home')  # or render same page with a success message

    return render(request, 'plantsapp/home.html')

def wishlist_count(request):
    if request.user.is_authenticated:
        count = WishlistItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'wishlist_count': count}

def cart_count(request):
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'cart_count': count}

def product_list_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all()

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True)

    return render(request, 'plantsapp/product_list.html', {
        'products': products,
        'wishlist_ids': list(wishlist_ids),
        'selected_category': category,
        'categories': categories,
    })


@require_POST
@login_required
def remove_from_wishlist(request, product_id):
    WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()
    return JsonResponse({'status': 'removed'})

from django.views.decorators.http import require_POST

@require_POST
@login_required
def update_cart_quantity(request, product_id):
    action = request.POST.get("action")
    cart_item = CartItem.objects.filter(user=request.user, product_id=product_id).first()

    if not cart_item:
        return JsonResponse({'error': 'Item not found'}, status=404)

    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()

    return JsonResponse({'status': 'success', 'quantity': cart_item.quantity if cart_item.pk else 0})


@require_POST
@login_required
def delete_cart_item(request, product_id):
    CartItem.objects.filter(user=request.user, product_id=product_id).delete()
    return JsonResponse({'status': 'deleted'})



@login_required
def clear_cart(request):
    if request.method == 'POST':
        CartItem.objects.filter(user=request.user).delete()
        return redirect('cart')
    return redirect('cart')

def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    tax = round(subtotal * Decimal("0.08"), 2)
    discount = round(subtotal * Decimal("0.1"), 2)
    total = round(subtotal + tax - discount, 2)

    return render(request, 'plantsapp/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'discount': discount,
        'total': total,
    })


@login_required
def profile_view(request):
    return render(request, 'plantsapp/profile.html', {'user': request.user})

@login_required
def manage_orders_view(request):
    return render(request, 'plantsapp/manage_orders.html')


def order_view(request):
    return render(request, 'plantsapp/order.html')