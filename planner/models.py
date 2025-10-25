from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.template.defaultfilters import slugify
import secrets, string
from urllib.parse import quote
from urllib.request import urlopen
import json
from multiselectfield import MultiSelectField

class Choices:
    def get_activity_kind():
        return (('BAR', 'Bar / Pub'), ("TRIVIA", "Trivia / Pub Quiz"), ("KARAOKE", "Karaoke"), 
                ("LIVE_MUSIC", "Live Music"), ("ACTIVITY", "Activity (pool, darts, bowling, etc.)"),
                ("CLUB", "Club"),  ("FOOD", "Food / Restaurant"), ("OTHER", "Other"))
    
    def get_budget_band():
        return (("LOW", "£"), ("MEDIUM", "££"), ("HIGH", "£££"))
    
    def get_best_days():
        return (("MON", "Monday"), ("TUE", "Tuesday"), ("WED", "Wednesday"), ("THU", "Thursday"),
                ("FRI", "Friday"), ("SAT", "Saturday"), ("SUN", "Sunday"))
    
    def get_occasion():
        return (("NONE", "Just a night out"), ("BIRTHDAY", "Birthday"),
                ("CHRISTMAS", "Christmas Night"), ("RETIREMENT", "Retirement Party"),
                ("CELEBRATION", "Big Win / Celebration"), ("WELCOME", "Welcome / Onboarding"),
                ("OTHER", "Other"))

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=Choices.get_activity_kind(), default=("OTHER", "Other"))
    city = models.CharField(max_length=100, default="Glasgow")
    postcode = models.CharField(max_length=12, blank=True)
    eastings = models.IntegerField(blank=True, default=0)
    northings = models.IntegerField(blank=True, default=0)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="venues")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    best_days = MultiSelectField(choices=Choices.get_best_days(), max_length=20)
    slug = models.SlugField(unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["city", "is_active"]),
            models.Index(fields=["kind"]),
            models.Index(fields=["name"]),
        ]
        ordering = ["name"]
        unique_together = [("name", "postcode")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        if self.pk:
            old = Venue.objects.get(pk=self.pk)
            if old.postcode != self.postcode:
                self.eastings, self.northings = self.get_coordinates(self.postcode)
        else:
            self.eastings, self.northings = self.get_coordinates(self.postcode)
        super().save(*args, **kwargs)

    def generate_unique_slug(self):
        alphabet = string.ascii_letters + string.digits
        while True:
            random_slug = ''.join(secrets.choice(alphabet) for i in range(16))
            if not Venue.objects.filter(slug=random_slug).exists():
                return random_slug

    def get_coordinates(self, postcode):
        try:
            postcode = quote(postcode)
            url = f"https://api.postcodes.io/postcodes/{postcode}"
            print(postcode)
            with urlopen(url) as response:
                data = json.load(response)
            result = data.get('result')
            if result:
                return result['eastings'], result['northings']
        except:
            pass
        return None, None

    def __str__(self):
        return self.name

class Event(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    budget = models.CharField(max_length=10, choices=Choices.get_budget_band(), default=("MEDIUM", "££"))

    min_group_size = models.PositiveIntegerField(default=2)
    max_group_size = models.PositiveIntegerField(null=True, blank=True, help_text="Null = no hard limit")
    booking_url = models.URLField(blank=True)

    tags = models.ManyToManyField(Tag, blank=True, related_name="events")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["budget"]),
            models.Index(fields=["is_active"]),
        ]
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} @ {self.venue.name}"

    @property
    def is_upcoming(self) -> bool:
        if not self.start:
            return False
        return self.start >= timezone.now()

    def fits_group(self, size: int) -> bool:
        if size < self.min_group_size:
            return False
        if self.max_group_size and size > self.max_group_size:
            return False
        return True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        if self.min_group_size and self.max_group_size:
            if self.max_group_size < self.min_group_size:
                self.max_group_size = self.min_group_size
        super().save(*args, **kwargs)

    def generate_unique_slug(self):
        alphabet = string.ascii_letters + string.digits
        while True:
            random_slug = ''.join(secrets.choice(alphabet) for i in range(16))
            if not Venue.objects.filter(slug=random_slug).exists():
                return random_slug