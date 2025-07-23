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



from .models import Product
from django.contrib.auth.decorators import login_required

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
    products = Product.objects.all()
    wishlist_ids = []

    if request.user.is_authenticated:
        wishlist_ids = WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True)

    return render(request, 'plantsapp/product_list.html', {
        'products': products,
        'wishlist_ids': list(wishlist_ids)  # Pass to template
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


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # name in your urls.py
    else:
        form = ProductForm()
    return render(request, 'plantsapp/add_product.html', {'form': form})


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