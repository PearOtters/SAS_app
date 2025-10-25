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
    # Check if user is already logged in
    if request.user.is_authenticated:
        return redirect('planner:index')
    
    if request.method == "POST":
        # Use Django's built-in AuthenticationForm
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                auth_login(request, user)  # Log the user in
                # Redirect to 'next' parameter if present, otherwise to 'index'
                next_url = request.POST.get('next') or reverse('planner:index')
                return redirect(next_url)
    else:
        form = AuthenticationForm()

    # Pass the form to the template
    return render(request, 'planner/login.html', {'form': form})

def user_register(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password') 
            user.set_password(password)
            user.save()
            
            return redirect(reverse('planner:index'))
        else:
            print(form.errors)
    else:
        form = UserForm()
    return render(request, 'planner/register.html', {'form': form})

@login_required
def user_logout(request):
    auth_logout(request)
    return redirect(reverse('planner:index'))

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