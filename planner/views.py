
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.utils import timezone
from .models import Venue, Event, EventOccurrence, Choices 
from .forms import * # Assuming all forms are imported here
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from datetime import datetime, timedelta 
import random
import json 
from decimal import Decimal 


class MockEvent:
    def __init__(self, title, slug, lat, lng, location_name):
        self.title = title
        self.slug = slug
        self.latitude = lat
        self.longitude = lng
        self.location_name = location_name

class MockEventOccurrence:
    
    def __init__(self, title, description, start_datetime, duration_hours, attendees, category, lat, lng, location_name):
        self.id = random.randint(100, 999) 
        self.start_datetime = start_datetime
        self.duration_hours = duration_hours
        self.actual_attendees = attendees
        
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
    if request.user.is_authenticated:
        return redirect('planner:dashboard')

    if request.method == "POST":
        form = UserForm(request.POST) 
        if form.is_valid():
            user = form.save() 
            auth_login(request, user)
            return redirect(reverse('planner:dashboard'))
        else:
            print(form.errors) 
            pass 
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
        event_name = request.POST.get('eventName')
        description = request.POST.get('eventDescription')
        
        date_str = request.POST.get('selected_date')
        time_str = request.POST.get('eventTime')
        duration_hours = request.POST.get('eventDuration')
        attendees = request.POST.get('eventAttendees')
        
        lat_str = request.POST.get('selectedLat')
        lng_str = request.POST.get('selectedLng')
        location_name = request.POST.get('locationName')

        if not all([event_name, date_str, time_str, lat_str, lng_str]):
            context['error'] = 'All required fields (Name, Date, Time, Location) must be provided.'
            return render(request, 'planner/eventCreation.html', context)
        
        try:
            start_datetime_str = f"{date_str} {time_str}"
            start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M')
            
            duration = Decimal(duration_hours) if duration_hours else Decimal(2.0)
            attendee_count = int(attendees) if attendees else 0
            
            lat = Decimal(lat_str)
            lng = Decimal(lng_str)
            
            new_event = Event.objects.create(
                title=event_name,
                description=description,
                latitude=lat,
                longitude=lng,
                location_name=location_name or f'({lat_str}, {lng_str})', 
                budget='MEDIUM', 
                min_group_size=max(1, attendee_count),
            )
            
            EventOccurrence.objects.create(
                event=new_event,
                start_datetime=start_datetime,
                duration_hours=duration,
                actual_attendees=attendee_count,
            )
            
            return redirect('planner:dashboard')

        except ValueError:
            context['error'] = 'Invalid number, time, or coordinate format provided.'
            return render(request, 'planner/eventCreation.html', context)
        except Exception as e:
            context['error'] = f'An unexpected error occurred during creation: {e}'
            return render(request, 'planner/eventCreation.html', context)
    
    return render(request, 'planner/eventCreation.html', context)


@login_required
def dashboard(request):
    
    search_name = request.GET.get('search_name')
    budget = request.GET.get('budget')
    kind = request.GET.get('kind') # NEW: Get the 'kind' filter
    min_attendees_str = request.GET.get('min_attendees')
    
    occurrences_queryset = EventOccurrence.objects.filter(
        start_datetime__gte=timezone.now() - timedelta(days=1)
    ).select_related('event').order_by('start_datetime')


    if search_name:
        occurrences_queryset = occurrences_queryset.filter(
            event__title__icontains=search_name
        )
    
    if budget and budget in [choice[0] for choice in Choices.get_budget_band()]:
        occurrences_queryset = occurrences_queryset.filter(
            event__budget=budget
        )
        
    if kind and kind in [choice[0] for choice in Choices.get_event_kind()]:
        occurrences_queryset = occurrences_queryset.filter(
            event__kind=kind
        )
    
    if min_attendees_str:
        try:
            min_attendees = int(min_attendees_str)
            occurrences_queryset = occurrences_queryset.filter(
                actual_attendees__gte=min_attendees
            )
        except ValueError:
            pass

    occurrences = occurrences_queryset 

    event_data_list = []
    
    if not occurrences.exists() and not (search_name or budget or kind or min_attendees_str): 
        print("Using mock event data for dashboard.")
        
        class MockEventInternal:
            def __init__(self, title, description, category, lat, lng, location_name, budget='MEDIUM'):
                self.title = title
                self.description = description
                self.category = category 
                self.latitude = lat
                self.longitude = lng
                self.location_name = location_name
                self.budget = budget
                self.min_group_size = 1

        class MockEventOccurrenceUpdated:
            def __init__(self, title, description, start_datetime, duration_hours, attendees, category, lat, lng, location_name, budget='MEDIUM'):
                self.id = random.randint(100, 999) 
                self.start_datetime = start_datetime
                self.duration_hours = duration_hours
                self.actual_attendees = attendees
                self.event = MockEventInternal(title, description, category, lat, lng, location_name, budget)

        mock_occurrences = [
            MockEventOccurrenceUpdated(
                title="Tech Conference 2025", 
                description="Annual technology conference.",
                start_datetime=datetime.now().replace(day=15, hour=9, minute=0, second=0, microsecond=0) + timedelta(days=30),
                duration_hours=Decimal(8), attendees=500, category='Conference',
                lat=55.8642, lng=-4.2518, location_name='Glasgow City Centre', budget='HIGH'
            ),
            MockEventOccurrenceUpdated(
                title="Design Workshop", 
                description="Hands-on workshop.",
                start_datetime=datetime.now().replace(day=18, hour=14, minute=0, second=0, microsecond=0) + timedelta(days=30),
                duration_hours=Decimal(3), attendees=30, category='Workshop',
                lat=55.8700, lng=-4.2600, location_name='West End Community Hall', budget='LOW'
            ),
        ]
        
        for occurrence in mock_occurrences:
            event_data_list.append({
                'id': occurrence.id,
                'name': occurrence.event.title,
                'date_ms': int(occurrence.start_datetime.timestamp() * 1000), 
                'time': occurrence.start_datetime.strftime('%H:%M'),
                'duration': float(occurrence.duration_hours),
                'category': occurrence.event.category,
                'attendees': occurrence.actual_attendees,
                'budget': occurrence.event.budget,
                'location': {
                    'lat': float(occurrence.event.latitude) if occurrence.event.latitude else 0.0,
                    'lng': float(occurrence.event.longitude) if occurrence.event.longitude else 0.0,
                    'address': occurrence.event.location_name,
                }
            })
    
    elif occurrences.exists():
        for occurrence in occurrences:
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
                'budget': event.budget,
                'location': {
                    'lat': float(event.latitude) if event.latitude else 0.0,
                    'lng': float(event.longitude) if event.longitude else 0.0,
                    'address': event.location_name,
                }
            })
        
    context = {
        'events_json': json.dumps(event_data_list), 
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
    venue = get_object_or_404(Venue, slug=venue_slug)
    
    context_dict = {'venue': venue}
    return HttpResponse(f"Venue page for: {venue.name}")