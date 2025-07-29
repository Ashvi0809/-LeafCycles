from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from .serializers import RegisterSerializer, LoginSerializer
from .models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import Product
from django.shortcuts import get_object_or_404
from .models import WishlistItem
from .forms import ProductForm
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import JsonResponse
from .models import CartItem
from django.db.models import Count
from django.views.decorators.http import require_POST
from .models import ContactMessage
from .models import Category
from .models import Review
from decimal import Decimal
from .models import Order
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
import jwt
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.middleware import get_user
import logging

logger = logging.getLogger(__name__)


def get_user_from_jwt_request(request):
    token = request.COOKIES.get('access_token')
    logger.debug(f"Access Token: {token}")
    if token:
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded.get("user_id")
            logger.debug(f"Decoded User ID: {user_id}")
            return CustomUser.objects.get(id=user_id)
        except (jwt.ExpiredSignatureError, jwt.DecodeError) as e:
            logger.error(f"JWT Decode Error: {str(e)}")
        except CustomUser.DoesNotExist:
            logger.error("User not exist")
    # Fallback to session authentication
    user = get_user(request)
    if user and user.is_authenticated:
        logger.debug(f"Fallback to session user: {user.email}")
        return user
    logger.warning("No access token or session user found")
    return None


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
            return redirect("/api/login/")
        else:
            return render(request, "plantsapp/signup.html", {"errors": serializer.errors})
    return render(request, "plantsapp/signup.html", {})


def login_form(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)  # Enable session authentication
            refresh = RefreshToken.for_user(user)
            response = redirect("/home/")
            token = str(refresh.access_token)
            response.set_cookie(
                'access_token',
                token,
                httponly=True,
                secure=False,  # Set to False for HTTP (dev), True for HTTPS
                samesite='Lax'
            )
            logger.debug(f"Set access_token cookie: {token}")
            return response
        else:
            return render(request, "plantsapp/login.html", {"error": "Invalid email or password"})
    return render(request, "plantsapp/login.html", {})


def home_view(request):
    user = get_user_from_jwt_request(request)
    context = {'user': user}
    if request.method == "POST":
        if user:
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
            return redirect('home')
    return render(request, 'plantsapp/home.html', context)


def forgot_password_form(request):
    return render(request, 'plantsapp/forgot_password.html', {})


def verify_otp_form(request):
    return render(request, 'plantsapp/verify_otp.html', {})


def reset_password_form(request):
    return render(request, 'plantsapp/reset_password.html', {})


def logout_view(request):
    logout(request)
    response = redirect('/')
    response.delete_cookie('access_token')
    return response


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
            response = Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            })
            response.set_cookie(
                'access_token',
                str(refresh.access_token),
                httponly=True,
                secure=False,  # Set to False for HTTP (dev), True for HTTPS
                samesite='Lax'
            )
            return response
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
    user = get_user_from_jwt_request(request)
    products = Product.objects.annotate(review_count=Count('reviews'))
    categories = Category.objects.all()
    wishlist_ids = []
    if user:
        wishlist_ids = WishlistItem.objects.filter(user=user).values_list('product_id', flat=True)
    context = {
        'products': products,
        'wishlist_ids': list(wishlist_ids),
        'categories': categories,
        'selected_category': None
    }
    return render(request, 'plantsapp/product_list.html', context)


def product_detail(request, pk):
    user = get_user_from_jwt_request(request)
    product = get_object_or_404(Product, pk=pk)
    in_wishlist = False
    if user:
        in_wishlist = WishlistItem.objects.filter(user=user, product=product).exists()
    context = {
        'product': product,
        'in_wishlist': in_wishlist
    }
    return render(request, 'plantsapp/product_detail.html', context)


@csrf_protect
def add_product(request):
    user = get_user_from_jwt_request(request)
    context = {'categories': Category.objects.all()}
    if request.method == 'POST' and user:
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        category = Category.objects.get(id=category_id)
        image = request.FILES.get('image')
        description = request.POST.get('description')
        price = request.POST.get('price')
        origin = request.POST.get('origin')
        material = request.POST.get('material')
        dimensions = request.POST.get('dimensions')
        weight = request.POST.get('weight')
        certification_name = request.POST.get('certification_name')
        shelf_life = request.POST.get('shelf_life')
        storage = request.POST.get('storage')
        features = []
        for key in request.POST:
            if key.startswith('feature_'):
                feature_value = request.POST.get(key)
                if feature_value:
                    features.append(feature_value)
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
            uploaded_by=user
        )
        return redirect('product_list')
    return render(request, 'plantsapp/add_product.html', context)


@csrf_exempt
def toggle_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
        user = get_user_from_jwt_request(request)
        if not user:
            return JsonResponse({'error': 'User not authenticated'}, status=403)
        wishlist_item, created = WishlistItem.objects.get_or_create(user=user, product=product)
        if not created:
            wishlist_item.delete()
            return JsonResponse({'status': 'removed'})
        else:
            return JsonResponse({'status': 'added'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


def wishlist_view(request):
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    context = {'wishlist_items': WishlistItem.objects.filter(user=user)}
    return render(request, 'plantsapp/wishlist.html', context)


@csrf_protect
def add_to_cart(request, product_id):
    user = get_user_from_jwt_request(request)
    if not user:
        if request.is_ajax():
            return JsonResponse({'error': 'User not authenticated', 'redirect': '/login-form/'}, status=403)
        return redirect('/login-form/')
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            if request.is_ajax():
                return JsonResponse({'error': 'Product not found'}, status=404)
            return redirect('product_list')
        cart_item, created = CartItem.objects.get_or_create(user=user, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        if request.is_ajax():
            cart_count = CartItem.objects.filter(user=user).count()
            return JsonResponse({
                'status': 'added',
                'cart_count': cart_count,
                'message': f'{product.name} added to cart'
            })
        return redirect('cart')
    if request.is_ajax():
        return JsonResponse({'error': 'Invalid request'}, status=400)
    return redirect('product_list')


def cart_view(request):
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    cart_items = CartItem.objects.filter(user=user)
    subtotal = sum(item.product.price * item.quantity for item in cart_items if item.product.price) or 0
    tax = round(subtotal * Decimal("0.08"), 2)
    discount = round(subtotal * Decimal("0.1"), 2)
    total = round(subtotal + tax - discount, 2)
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'discount': discount,
        'total': total,
    }
    return render(request, 'plantsapp/cart.html', context)


def landing_page(request):
    user = get_user_from_jwt_request(request)
    context = {'user': user}
    return render(request, 'plantsapp/landing.html', context)


@require_POST
@csrf_protect
def rate_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    rating = int(request.POST.get("rating"))
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    review, created = Review.objects.get_or_create(user=user, product=product)
    review.rating = rating
    review.save()
    return redirect("product_list")


def wishlist_count(request):
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    if user:
        count = WishlistItem.objects.filter(user=user).count()
    else:
        count = 0
    return {'wishlist_count': count}


def cart_count(request):
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    if user:
        count = CartItem.objects.filter(user=user).count()
    else:
        count = 0
    return {'cart_count': count}


def product_list_by_category(request, category_id):
    user = get_user_from_jwt_request(request)
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all()
    wishlist_ids = []
    if user:
        wishlist_ids = WishlistItem.objects.filter(user=user).values_list('product_id', flat=True)
    context = {
        'products': products,
        'wishlist_ids': list(wishlist_ids),
        'selected_category': category,
        'categories': categories,
    }
    return render(request, 'plantsapp/product_list.html', context)


@require_POST
@csrf_protect
def remove_from_wishlist(request, product_id):
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    WishlistItem.objects.filter(user=user, product_id=product_id).delete()
    return JsonResponse({'status': 'removed'})


@require_POST
@csrf_protect
def update_cart_quantity(request, product_id):
    action = request.POST.get("action")
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    cart_item = CartItem.objects.filter(user=user, product_id=product_id).first()
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
@csrf_protect
def delete_cart_item(request, product_id):
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    CartItem.objects.filter(user=user, product_id=product_id).delete()
    return JsonResponse({'status': 'deleted'})


@require_POST
@csrf_protect
def clear_cart(request):
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    CartItem.objects.filter(user=user).delete()
    return redirect('cart')


def profile_view(request):
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    context = {'user': user}
    return render(request, 'plantsapp/profile.html', context)


@method_decorator(login_required, name='dispatch')
class manage_orders_view(View):
    def get(self, request):
        user = request.user
        orders = Order.objects.filter(product__uploaded_by=user).select_related('product', 'buyer')
        total_orders = orders.count()
        pending_orders = orders.filter(status='pending').count()
        shipped_orders = orders.filter(status='shipped').count()
        total_revenue = sum(order.total_amount for order in orders)
        order_data = []
        for order in orders:
            order_data.append({
                'id': order.id,
                'customer_name': order.buyer.name,
                'customer_email': order.buyer.email,
                'product_name': order.product.name,
                'product_sku': f"P{order.product.id:03}",
                'quantity': order.quantity,
                'amount': order.total_amount,
                'status': order.status,
                'created_at': order.created_at,
            })
        return render(request, 'plantsapp/manage_orders.html', {
            'orders': order_data,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'shipped_orders': shipped_orders,
            'total_revenue': total_revenue,
        })


@require_POST
@csrf_protect
def create_order(request):
    user = get_user_from_jwt_request(request)
    if not user:
        return JsonResponse({'error': 'User not authenticated', 'redirect': '/login-form/'}, status=403)

    cart_items = CartItem.objects.filter(user=user)
    if not cart_items:
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    try:
        for item in cart_items:
            if not item.product.price:
                return JsonResponse({'error': f'Price not set for {item.product.name}'}, status=400)
            total_amount = item.product.price * item.quantity
            Order.objects.create(
                buyer=user,
                product=item.product,
                quantity=item.quantity,
                total_amount=total_amount,
                status='pending'
            )
        CartItem.objects.filter(user=user).delete()
        return JsonResponse({'status': 'success', 'message': 'Order placed successfully'})
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return JsonResponse({'error': 'An error occurred while placing the order'}, status=500)


def order_view(request):
    user = get_user_from_jwt_request(request)
    if not user:
        return redirect('/login-form/')
    orders = Order.objects.filter(buyer=user).select_related('product').order_by('-created_at')
    context = {
        'user': user,
        'orders': orders,
    }
    return render(request, 'plantsapp/order.html', context)


@require_POST
@csrf_protect
def reorder_items(request, order_id):
    user = get_user_from_jwt_request(request)
    if not user:
        return JsonResponse({'error': 'User not authenticated', 'redirect': '/login-form/'}, status=403)
    order = get_object_or_404(Order, id=order_id, buyer=user)
    try:
        cart_item, created = CartItem.objects.get_or_create(user=user, product=order.product)
        if not created:
            cart_item.quantity += order.quantity
        else:
            cart_item.quantity = order.quantity
        cart_item.save()
        return JsonResponse({'status': 'success', 'message': 'Items added to cart'})
    except Exception as e:
        logger.error(f"Error reordering: {str(e)}")
        return JsonResponse({'error': 'Failed to add items to cart'}, status=500)


@require_POST
@csrf_protect
def cancel_order(request, order_id):
    user = get_user_from_jwt_request(request)
    if not user:
        return JsonResponse({'error': 'User not authenticated', 'redirect': '/login-form/'}, status=403)
    order = get_object_or_404(Order, id=order_id, buyer=user)
    if order.status != 'pending':
        return JsonResponse({'error': 'Only pending orders can be cancelled'}, status=400)
    try:
        order.status = 'cancelled'
        order.save()
        return JsonResponse({'status': 'success', 'message': 'Order cancelled successfully'})
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        return JsonResponse({'error': 'Failed to cancel order'}, status=500)