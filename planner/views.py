
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.utils import timezone
# Venue is still imported but not used in event creation logic
from .models import Venue, Event, EventOccurrence, Choices 
from .forms import * # Assuming all forms are imported here
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from datetime import datetime, timedelta 
import random
import json 
from decimal import Decimal 

# --- Mocking Classes (Simplified to remove Venue dependency) ---

class MockEvent:
    """Mimics the Event model attributes needed by the dashboard template."""
    def __init__(self, title, slug, lat, lng, location_name):
        self.title = title
        self.slug = slug
        self.latitude = lat
        self.longitude = lng
        self.location_name = location_name

class MockEventOccurrence:
    """Mimics the EventOccurrence attributes needed by the dashboard template, 
    including related Event data."""
    
    def __init__(self, title, description, start_datetime, duration_hours, attendees, category, lat, lng, location_name):
        self.id = random.randint(100, 999) 
        self.start_datetime = start_datetime
        self.duration_hours = duration_hours
        self.actual_attendees = attendees
        
        # 1. Create MockEvent instance with location data
        class MockEventInternal:
            def __init__(self, title, description, category, lat, lng, location_name):
                self.title = title
                self.description = description
                self.category = category 
                self.latitude = lat
                self.longitude = lng
                self.location_name = location_name
                self.budget = 'MEDIUM'
                self.min_group_size = 1
                
        self.event = MockEventInternal(title, description, category, lat, lng, location_name)

# --- Helper Function (Removed serialize_venues) ---

# --- Views ---

def redirect_to_index(request):
    return redirect('planner:index')

def index(request):
    if request.user.is_authenticated:
        return redirect('planner:dashboard')
    
    template = loader.get_template("planner/index.html")
    return HttpResponse(template.render())

def user_login(request):
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
def create_event(request):
    
    context = {
        'error': None
    }
    
    if request.method == 'POST':
        # 1. Gather form data
        event_name = request.POST.get('eventName')
        description = request.POST.get('eventDescription')
        
        date_str = request.POST.get('selected_date')
        time_str = request.POST.get('eventTime')
        duration_hours = request.POST.get('eventDuration')
        attendees = request.POST.get('eventAttendees')
        
        # NEW LOCATION DATA
        lat_str = request.POST.get('selectedLat')
        lng_str = request.POST.get('selectedLng')
        location_name = request.POST.get('locationName')

        # Simple Validation: Date, Time, Name, and Coordinates are required
        if not all([event_name, date_str, time_str, lat_str, lng_str]):
            context['error'] = 'All required fields (Name, Date, Time, Location) must be provided.'
            return render(request, 'planner/eventCreation.html', context)
        
        try:
            # Type Conversion
            start_datetime_str = f"{date_str} {time_str}"
            start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M')
            
            duration = Decimal(duration_hours) if duration_hours else Decimal(2.0)
            attendee_count = int(attendees) if attendees else 0
            
            lat = Decimal(lat_str)
            lng = Decimal(lng_str)
            
            # 2. Create the Event object with location fields
            new_event = Event.objects.create(
                title=event_name,
                description=description,
                latitude=lat,
                longitude=lng,
                # Use the locationName from the search, or fall back to coordinates if clicked on map
                location_name=location_name or f'({lat_str}, {lng_str})', 
                budget='MEDIUM', 
                min_group_size=max(1, attendee_count),
            )
            
            # 3. Create the Event Occurrence object
            EventOccurrence.objects.create(
                event=new_event,
                start_datetime=start_datetime,
                duration_hours=duration,
                actual_attendees=attendee_count,
            )
            
            # 4. Success!
            return redirect('planner:dashboard')

        except ValueError:
            context['error'] = 'Invalid number, time, or coordinate format provided.'
            return render(request, 'planner/eventCreation.html', context)
        except Exception as e:
            context['error'] = f'An unexpected error occurred during creation: {e}'
            return render(request, 'planner/eventCreation.html', context)
    
    # GET request: render the empty form
    return render(request, 'planner/eventCreation.html', context)

## Existing Dashboard and Detail Views (Updated)

@login_required
def dashboard(request):
    
    # --- NEW: Get filter parameters from GET request ---
    search_name = request.GET.get('search_name')
    budget = request.GET.get('budget')
    min_attendees_str = request.GET.get('min_attendees')
    
    # Start with the base queryset
    occurrences_queryset = EventOccurrence.objects.filter(
        start_datetime__gte=timezone.now() - timedelta(days=1)
    ).select_related('event').order_by('start_datetime')

    # --- NEW: Apply Filters ---

    # 1. Search by Name
    if search_name:
        occurrences_queryset = occurrences_queryset.filter(
            event__title__icontains=search_name # Case-insensitive partial match on Event title
        )
    
    # 2. Filter by Budget
    if budget and budget in [choice[0] for choice in Choices.get_budget_band()]:
        occurrences_queryset = occurrences_queryset.filter(
            event__budget=budget # Match on Event budget field
        )
    
    # 3. Filter by Minimum Attendees
    if min_attendees_str:
        try:
            min_attendees = int(min_attendees_str)
            # Filter occurrences where actual attendees meet the minimum requested
            occurrences_queryset = occurrences_queryset.filter(
                actual_attendees__gte=min_attendees
            )
        except ValueError:
            # Handle invalid input (optional: add error message to context)
            pass

    # Update Query: use the filtered queryset
    occurrences = occurrences_queryset 

    event_data_list = []
    
    if not occurrences.exists() and not (search_name or budget or min_attendees_str): 
        # Only inject mock data if NO filters are applied AND no real events exist
        # If filters are applied and no results, we show an empty list which is correct.
        print("Using mock event data for dashboard.")
        
        # ... (rest of the mock data injection remains the same)
        # Note: Mock data logic doesn't inherently support filtering without client-side JS
        # filtering, but the server-side filtering is the priority for the database query.

        mock_occurrences = [
            MockEventOccurrence(
                title="Tech Conference 2025", 
                description="Annual technology conference.",
                start_datetime=datetime.now().replace(day=15, hour=9, minute=0, second=0, microsecond=0) + timedelta(days=30),
                duration_hours=Decimal(8), attendees=500, category='conference',
                lat=55.8642, lng=-4.2518, location_name='Glasgow City Centre'
            ),
            MockEventOccurrence(
                title="Design Workshop", 
                description="Hands-on workshop.",
                start_datetime=datetime.now().replace(day=18, hour=14, minute=0, second=0, microsecond=0) + timedelta(days=30),
                duration_hours=Decimal(3), attendees=30, category='workshop',
                lat=55.8700, lng=-4.2600, location_name='West End Community Hall'
            ),
        ]
        
        # ... (rest of the mock data loop)
        for occurrence in mock_occurrences:
            # ... (append to event_data_list)
            event_data_list.append({
                'id': occurrence.id,
                'name': occurrence.event.title,
                'date_ms': int(occurrence.start_datetime.timestamp() * 1000), 
                'time': occurrence.start_datetime.strftime('%H:%M'),
                'duration': float(occurrence.duration_hours),
                'category': occurrence.event.category,
                'attendees': occurrence.actual_attendees,
                'location': {
                    'lat': float(occurrence.event.latitude) if occurrence.event.latitude else 0.0,
                    'lng': float(occurrence.event.longitude) if occurrence.event.longitude else 0.0,
                    'address': occurrence.event.location_name,
                }
            })
    
    # If using REAL data, the events will be filtered by the queryset:
    elif occurrences.exists():
        # Format real database data for the front-end
        for occurrence in occurrences:
            # ... (loop remains the same)
            event = occurrence.event
            event_data_list.append({
                'id': occurrence.pk,
                'name': event.title,
                'date_ms': int(occurrence.start_datetime.timestamp() * 1000),
                'time': occurrence.start_datetime.strftime('%H:%M'),
                'duration': float(occurrence.duration_hours),
                'category': event.category, 
                'attendees': occurrence.actual_attendees,
                'description': event.description,
                'location': {
                    'lat': float(event.latitude) if event.latitude else 0.0,
                    'lng': float(event.longitude) if event.longitude else 0.0,
                    'address': event.location_name,
                }
            })
        
    context = {
        'events_json': json.dumps(event_data_list), 
        # NEW: You might want to pass back the search/filter terms to pre-populate the form
        # However, the HTML modification above already handles this using request.GET directly.
    }
    return render(request, 'planner/dashboard.html', context)


def view_event(request, event_slug):
    try:
        event = Event.objects.get(slug=event_slug)
    except Event.DoesNotExist:
        event = None
    context_dict = {
        'event': event,
        'event_slug': event_slug }
    return render(request, "planner/view_event.html", context=context_dict)

def view_venue(request, venue_slug):
    # This view still works as it only uses the Venue model
    venue = get_object_or_404(Venue, slug=venue_slug)
    
    context_dict = {'venue': venue}
    return HttpResponse(f"Venue page for: {venue.name}")