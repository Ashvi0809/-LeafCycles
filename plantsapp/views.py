from django.shortcuts import render
from .models import Plant

def plant_list(request):
    plants = Plant.objects.all()
    return render(request, 'plantsapp/plant_list.html', {'plants': plants})
