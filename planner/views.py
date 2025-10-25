from django.shortcuts import render
from django.shortcuts import redirect
from django.http.response import HttpResponse

# Create your views here.

def redirect_to_index(request):
    return redirect('planner:index')

def index(request):
    return HttpResponse("Hopefully this works")
