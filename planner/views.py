from django.shortcuts import render
from django.shortcuts import redirect
from django.http.response import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template import loader

# Create your views here.

def redirect_to_index(request):
    return redirect('planner:index')

def index(request):
    template = loader.get_template("planner/index.html")
    return HttpResponse(template.render())


def login(request):
    pass

def register(request):
    pass

@login_required
def logout(request):
    pass

