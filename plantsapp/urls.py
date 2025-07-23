from django.urls import path
from .views import (
    signup_form,
    login_form,
    home_view,
    forgot_password_form,
    verify_otp_form,
    reset_password_form,
    RegisterView,
    LoginView,
    ForgotPasswordView,
    VerifyOTPView,
    ResetPasswordView,
    product_list,
    product_detail
)
from . import views
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # HTML Form Views
    path('signup-form/', signup_form, name='signup-form'),
    path('login-form/', login_form, name='login-form'),
    path('home/', home_view, name='home'),
    path('forgot-password-form/', forgot_password_form, name='forgot-password-form'),
    path('verify-otp-form/', verify_otp_form, name='verify-otp-form'),
    path('reset-password-form/', reset_password_form, name='reset-password-form'),
    path('products/', product_list, name='product_list'),
    path('products/<int:pk>/', product_detail, name='product_detail'),
    path('add-product/', views.add_product, name='add-product'),
    path('wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
path('', views.landing_page, name='landing'),
    path('', views.landing_page, name='landing'),



]
