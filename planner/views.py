from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template import loader
from planner.models import *
from planner.forms import *
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from datetime import datetime # Needed for Mocking

class MockVenue:
    """Mimics the Venue model attributes needed by the dashboard template."""
    def __init__(self, name, slug):
        self.name = name
        self.slug = slug
class MockEvent:
    """Mimics the Event model attributes needed by the dashboard template."""
    def __init__(self, title, slug, venue_name):
        self.title = title
        self.slug = slug
        # Create a mock venue instance for the foreign key relationship
        self.venue = MockVenue(venue_name, slug.replace('-', '_')) 
# ---------------------------------

# Create your views here.

def redirect_to_index(request):
    return redirect('planner:index')

def index(request):
    # This view acts as a router: Public Welcome Page
    if request.user.is_authenticated:
        return redirect('planner:dashboard')
    
    # If not logged in, serve the public index.html page
    template = loader.get_template("planner/index.html")
    return HttpResponse(template.render())

def user_login(request):
    # Check if user is already logged in
    if request.user.is_authenticated:
        return redirect('planner:dashboard')
    
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                auth_login(request, user)
                return redirect(reverse('planner:dashboard'))
    else:
        form = AuthenticationForm()

    return render(request, 'planner/login.html', {'form': form})

def user_register(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password') 
            user.set_password(password)
            user.save()
            return redirect(reverse('planner:dashboard'))
        else:
            print(form.errors)
    else:
        form = UserForm()
    return render(request, 'planner/register.html', {'form': form})

@login_required
def user_logout(request):
    auth_logout(request)
    return redirect(reverse('planner:index'))


@login_required
def dashboard(request):
    # 1. Attempt to fetch real events
    events = Event.objects.filter(is_active=True).select_related('venue')
    
    # 2. Check if the database query returned results
    if not events.exists():
        # --- MOCK DATA INJECTION ---
        # Create four random events if the database is empty
        mock_events_data = [
            ("Glasgow Pub Quiz Night", "quiz-night", "The Old College Bar"),
            ("Live Jazz & Blues", "live-jazz", "The Blue Arrow"),
            ("Tech & VR Gaming Meetup", "vr-meetup", "Argyle Street VR Hub"),
            ("West End Food Festival", "food-fest", "Kelvingrove Park"),
        ]
        
        # Instantiate MockEvent objects
        events = [MockEvent(t, s, v) for t, s, v in mock_events_data]
        
    # -----------------------------

    context = {
        'events': events,
    }
    return render(request, 'planner/dashboard.html', context)

def view_event(request, event_slug):
    """
    Retrieves a single Event object using its slug.
    """
    try:
        event = Event.objects.get(slug=event_slug)
    except Event.DoesNotExist:
        event = None
    context_dict = {
        'event': event,
        'event_slug': event_slug }
    return render(request, "planner/view_event.html", context=context_dict)

def view_venue(request, venue_slug):
    """
    Retrieves a single Venue object using its slug.
    """
    venue = get_object_or_404(Venue, slug=venue_slug)
    
    context_dict = {'venue': venue}
    return HttpResponse(f"Venue page for: {venue.name}")
