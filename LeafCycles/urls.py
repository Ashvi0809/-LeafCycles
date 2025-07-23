from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("plantsapp.urls")),  # Routes all form and API views
path('', include('plantsapp.urls')),  # include app's urls only here!
]
