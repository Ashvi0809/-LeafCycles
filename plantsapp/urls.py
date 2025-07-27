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
    product_detail,
    add_product,
    toggle_wishlist,
    wishlist_view,
    add_to_cart,
    cart_view,
    landing_page,
    rate_product,
    product_list_by_category,
    profile_view,
    add_product,
    product_list_by_category,
    remove_from_wishlist,
    update_cart_quantity,
    delete_cart_item,
    clear_cart,
manage_orders_view,
)
from . import views
from .views import order_view

urlpatterns = [
    # HTML Form Views
    path('signup-form/', signup_form, name='signup-form'),
    path('login-form/', login_form, name='login-form'),
    path('home/', home_view, name='home'),
    path('forgot-password-form/', forgot_password_form, name='forgot-password-form'),
    path('verify-otp-form/', verify_otp_form, name='verify-otp-form'),
    path('reset-password-form/', reset_password_form, name='reset-password-form'),

    # Product Views
    path('products/', product_list, name='product_list'),
    path('products/<int:pk>/', product_detail, name='product_detail'),
    path('add-product/', add_product, name='add-product'),
path('products/category/<int:category_id>/',product_list_by_category, name='products_by_category'),

    # Wishlist & Cart
    path('wishlist/<int:product_id>/', toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
    path('rate/<int:product_id>/', rate_product, name='rate_product'),
    path('wishlist/remove/<int:product_id>/',remove_from_wishlist, name='remove_from_wishlist'),
    path('cart/update/<int:product_id>/', update_cart_quantity, name='update_cart_quantity'),
    path('cart/delete/<int:product_id>/', delete_cart_item, name='delete_cart_item'),
    path('cart/clear/', clear_cart, name='clear_cart'),

    path('api/add-to-cart/<int:product_id>/',add_to_cart, name='add_to_cart'),


    #  Landing Page
    path('', landing_page, name='landing'),

    path('profile/', profile_view, name='profile'),
    path('add-product/', add_product, name='add_product'),
        path('manage-orders/', manage_orders_view, name='manage_orders'),
        path('order/', order_view, name='order'),


]
from django.conf import settings
from django.conf.urls.static import static


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
