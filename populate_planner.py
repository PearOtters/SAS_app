import os
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sas_app.settings') 
django.setup()

from planner.models import Event, EventOccurrence, Tag, Choices
from django.utils import timezone


GLASGOW_LOCATIONS = [
    ("OVO Hydro / SEC Campus", Decimal('55.8601'), Decimal('-4.2882')),
    ("Glasgow Royal Concert Hall", Decimal('55.8647'), Decimal('-4.2541')),
    ("Platform Glasgow (The Arches)", Decimal('55.8569'), Decimal('-4.2498')),
    ("Òran Mór, West End", Decimal('55.8790'), Decimal('-4.2891')),
    ("Topgolf Glasgow", Decimal('55.8290'), Decimal('-4.2100')),
    ("Drygate Brewing Co.", Decimal('55.8655'), Decimal('-4.2380')),
    ("Kelvingrove Art Gallery and Museum", Decimal('55.8722'), Decimal('-4.2936')),
    ("SWG3, West End", Decimal('55.8660'), Decimal('-4.3000')),
    ("Glasgow Science Centre", Decimal('55.8576'), Decimal('-4.2929')),
    ("Gallery of Modern Art (GoMA)", Decimal('55.8596'), Decimal('-4.2520')),
]

EVENT_TEMPLATES = [
    ("Team Golf Challenge at Topgolf", "Casual fun with food and drinks in private bays for team bonding.", "MEDIUM", 8, 40, 3.0, 'ACTIVITY'), 
    ("Escape Room: The Glasgow Vaults", "High-pressure, fun team problem-solving challenge.", "MEDIUM", 6, 20, 2.0, 'ACTIVITY'), 
    ("Brewery Tour and Tasting at Drygate", "A guided tour followed by craft beer sampling and networking.", "MEDIUM", 15, 60, 2.5, 'FOOD'),
    ("Office Olympics: Fun & Games Day", "Internal corporate sports day with competitive, fun challenges.", "LOW", 30, 150, 6.0, 'SOCIAL'),
    ("Cocktail Making Masterclass", "Hands-on session learning to mix classic drinks.", "HIGH", 10, 30, 2.0, 'FOOD'),
    
    ("Q3 Results & Strategy Conference", "Full-day presentation of financial and strategic plans for the next quarter.", "HIGH", 100, 500, 7.0, 'CONFERENCE'),
    ("Advanced Python Development Workshop", "Half-day technical training for the software team.", "MEDIUM", 10, 25, 4.0, 'WORKSHOP'),
    ("Board Meeting: Annual Review", "Formal meeting of the company's board of directors.", "LOW", 5, 12, 3.0, 'MEETING'),
    ("Design Thinking Training Session", "Interactive workshop focused on problem-solving methodologies.", "MEDIUM", 15, 30, 4.5, 'WORKSHOP'),
    
    ("Candlelight: The Best of Hans Zimmer", "Film score classics performed by a string ensemble.", "MEDIUM", 50, 200, 1.5, 'CONCERT'),
    ("Ardal O'Hanlon Live Stand-up", "A comedy show at a central theatre venue.", "MEDIUM", 80, 400, 2.0, 'COMEDY'),
    ("Modern Scottish Art Exhibition Launch", "Evening reception for a new gallery installation.", "LOW", 20, 100, 3.0, 'EXHIBITION'),
    ("The Little Mermaid (Pantomime)", "Annual Christmas pantomime show.", "HIGH", 100, 600, 2.5, 'THEATRE'),
    
    ("Team Social Mixer: Finnieston Edition", "A company-wide networking event with drinks and appetizers.", "MEDIUM", 30, 80, 3.0, 'SOCIAL'),
    ("Day Fever Glasgow Disco", "Daytime disco and social event for a casual Friday afternoon.", "LOW", 50, 200, 5.0, 'SOCIAL'),
    ("Riverside Museum Tour", "Guided visit to Glasgow's transport museum.", "LOW", 5, 15, 2.0, 'TOUR'),
    ("The Ultimate 90s Rave Night", "Throwback club night for staff and friends.", "MEDIUM", 150, 800, 5.0, 'CLUB'),
    
    ("Monthly Book Club Meetup", "Discussion of the latest novel, held in a cafe space.", "LOW", 5, 15, 1.5, 'MEETING'),
    ("First Aid Certification Course", "Mandatory all-day safety training.", "HIGH", 10, 20, 8.0, 'WORKSHOP'),
    ("Sales Team Karaoke Night", "Casual night out for the sales department.", "MEDIUM", 10, 30, 4.0, 'CLUB'),
    ("Client Appreciation Dinner", "Formal dinner event for key partners and clients.", "HIGH", 20, 50, 3.0, 'FOOD'),
    ("Historic Tours of Glasgow University", "A walking tour of the historic university campus.", "LOW", 5, 25, 2.5, 'TOUR'),
    ("Cyber Security Webinar Viewing", "Group viewing of a live security webinar.", "LOW", 10, 30, 1.0, 'MEETING'),
    ("Annual General Meeting (AGM)", "Statutory meeting for shareholders.", "HIGH", 50, 200, 4.0, 'CONFERENCE'),
    ("Data Analysis Refresher Course", "Mid-level training for analysts.", "MEDIUM", 8, 18, 3.0, 'WORKSHOP'),
]


def populate():
    print("Starting planner database population (using get_or_create)...")
    
    EventOccurrence.objects.all().delete()
    print("Existing Event Occurrence data cleared.")
    
    tag_names = ['Team Building', 'Corporate', 'Social', 'Training', 'Entertainment']
    tags = {}
    for name in tag_names:
        tag, created = Tag.objects.get_or_create(name=name)
        tags[slugify(name)] = tag
        if created:
            print(f"Created tag: {name}")
            
    print("Tags confirmed/created.")

    current_date = timezone.now().date()
    start_date = current_date + timedelta(days=random.randint(2, 5))
    
    created_occurrences_count = 0
    
    for i, template in enumerate(EVENT_TEMPLATES):
        
        title, description, budget, min_size, max_size, duration, kind = template
        
        if 'Topgolf' in title:
            location_name, lat, lng = GLASGOW_LOCATIONS[4]
        elif 'Drygate' in title:
            location_name, lat, lng = GLASGOW_LOCATIONS[5]
        elif 'Conference' in title or 'AGM' in title:
            location_name, lat, lng = GLASGOW_LOCATIONS[0]
        else:
            location_name, lat, lng = random.choice(GLASGOW_LOCATIONS)
        
        final_title = title
        
        try:
            new_event, event_created = Event.objects.get_or_create(
                title=final_title,
                location_name=location_name,
                kind=kind,
                defaults={
                    'description': description,
                    'latitude': lat,
                    'longitude': lng,
                    'budget': budget,
                    'min_group_size': min_size,
                    'max_group_size': max_size,
                }
            )
            
            if event_created:
                print(f"Created new event: {final_title}")
                
            event_tags_to_set = []
            if kind in ['ACTIVITY', 'SOCIAL', 'FOOD']:
                event_tags_to_set.append(tags['social'])
                if 'Challenge' in title or 'Olympics' in title or 'Escape' in title:
                     event_tags_to_set.append(tags['team_building'])
            if kind in ['CONFERENCE', 'MEETING']:
                event_tags_to_set.append(tags['corporate'])
            if kind in ['WORKSHOP']:
                event_tags_to_set.append(tags['training'])
            if kind in ['CONCERT', 'COMEDY', 'THEATRE', 'CLUB']:
                 event_tags_to_set.append(tags['entertainment'])
            
            new_event.tags.set(event_tags_to_set)

            start_time_offset = timedelta(days=random.randint(0, 30) + i // 4, 
                                          hours=random.randint(9, 21), 
                                          minutes=random.choice([0, 30]))
            occurrence_datetime = datetime.combine(start_date, datetime.min.time()) + start_time_offset
            occurrence_datetime = timezone.make_aware(occurrence_datetime)
            
            occurrence, occurrence_created = EventOccurrence.objects.get_or_create(
                event=new_event,
                start_datetime=occurrence_datetime,
                defaults={
                    'duration_hours': Decimal(duration),
                    'actual_attendees': random.randint(min_size, min(max_size if max_size else min_size * 3, 500)),
                }
            )
            
            if occurrence_created:
                created_occurrences_count += 1

        except Exception as e:
            print(f"Error processing event {final_title}: {e}")
            continue

    print("-" * 50)
    print(f"Database population complete! Created {created_occurrences_count} new Event Occurrences.")
    if EventOccurrence.objects.exists():
        print(f"Total Events in DB: {Event.objects.count()}")
        print(f"Next event starts on: {EventOccurrence.objects.order_by('start_datetime').first().start_datetime.strftime('%Y-%m-%d %H:%M')}")
    print("-" * 50)


if __name__ == '__main__':
    if 'your_project_name' in os.environ.get('DJANGO_SETTINGS_MODULE', ''):
        print("ERROR: Please update 'your_project_name.settings' in the script to your actual Django project name.")
    else:
        populate()