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
    return render(request, 'plantsapp/product_list.html', {'products': products})