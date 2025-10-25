from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.http.response import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template import loader
from planner.models import *
from planner.forms import *
from django.contrib.auth import authenticate, login, logout

# Create your views here.

def redirect_to_index(request):
    return redirect('planner:index')

def index(request):
    template = loader.get_template("planner/index.html")
    return HttpResponse(template.render())


def user_login(request):
    pass

def user_register(request):
    form = UserForm()
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            raw_password = form.cleaned_data['password']
            user.password = raw_password
            user.save()
            user = authenticate(username=user.username, password=raw_password)
            if user is not None:
                login(request, user)
            return redirect(reverse('planner:index'))
        else:
            print(form.errors)
    return render(request, 'planner/register.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect(reverse('index'))

def view_event(request, event_slug):
    context_dict = {}
    try:
        event = Event.objects.get(slug=event_slug)
        context_dict['event'] = event
    except Event.DoesNotExist:
        context_dict['event'] = None
    return render(request, "planner/view_event", context=context_dict)

def view_venue(request, event_slug):
    pass