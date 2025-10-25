from django.db import models
from __future__ import annotations
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


# ---------- Choice Enums ----------

class ActivityKind(models.TextChoices):
    BAR = "BAR", "Bar / Pub"
    TRIVIA = "TRIVIA", "Trivia / Pub Quiz"
    KARAOKE = "KARAOKE", "Karaoke"
    LIVE_MUSIC = "LIVE_MUSIC", "Live Music"
    ACTIVITY = "ACTIVITY", "Activity (pool, darts, bowling, etc.)"
    HIDDEN_GEM = "HIDDEN_GEM", "Hidden Gem"
    FOOD = "FOOD", "Food / Restaurant"
    OTHER = "OTHER", "Other"


class BudgetBand(models.TextChoices):
    LOW = "LOW", "£"
    MEDIUM = "MEDIUM", "££"
    HIGH = "HIGH", "£££"


class Occasion(models.TextChoices):
    NONE = "NONE", "Just a night out"
    BIRTHDAY = "BIRTHDAY", "Birthday"
    CHRISTMAS = "CHRISTMAS", "Christmas Night"
    RETIREMENT = "RETIREMENT", "Retirement Party"
    CELEBRATION = "CELEBRATION", "Big Win / Celebration"
    WELCOME = "WELCOME", "Welcome / Onboarding"
    OTHER = "OTHER", "Other"


class DataSourceType(models.TextChoices):
    HARDCODED = "HARDCODED", "Hardcoded"
    SCRAPED = "SCRAPED", "Scraped"
    PUBLIC_API = "PUBLIC_API", "Public API"


# ---------- Core Catalog ----------

class Tag(models.Model):
    """
    Generic tags for filtering and flavor (e.g., 'cocktails', 'quiet', 'late-night', 'BYOB').
    """
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Venue(models.Model):
    """
    A place in/around Glasgow where an office night out can happen.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=ActivityKind.choices, default=ActivityKind.BAR)

    # Location
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, default="Glasgow")
    postcode = models.CharField(max_length=12, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Contact & web
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    place_id = models.CharField(max_length=128, blank=True, help_text="External place identifier (e.g., Google).")

    # Metadata
    tags = models.ManyToManyField(Tag, blank=True, related_name="venues")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["city", "is_active"]),
            models.Index(fields=["kind"]),
            models.Index(fields=["name"]),
        ]
        ordering = ["name"]
        unique_together = [("name", "address")]

    def __str__(self) -> str:
        return self.name


class Event(models.Model):
    """
    A dated thing at a venue (quiz night, karaoke, live set, limited offer, etc.).
    Can also represent an 'evergreen' activity by leaving end time null and/or using rrule.
    """
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    rrule = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional iCal RRULE like 'FREQ=WEEKLY;BYDAY=TH;BYHOUR=19'.",
    )

    kind = models.CharField(max_length=20, choices=ActivityKind.choices, default=ActivityKind.OTHER)
    budget = models.CharField(max_length=10, choices=BudgetBand.choices, default=BudgetBand.MEDIUM)

    min_group_size = models.PositiveIntegerField(default=2)
    max_group_size = models.PositiveIntegerField(null=True, blank=True, help_text="Null = no hard limit")
    booking_url = models.URLField(blank=True)

    # Quality & popularity signals
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    rating_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name="events")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["start"]),
            models.Index(fields=["kind"]),
            models.Index(fields=["budget"]),
            models.Index(fields=["is_active"]),
        ]
        ordering = ["start", "title"]

    def __str__(self) -> str:
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


class Offer(models.Model):
    """
    Optional deals tied to a venue or event (e.g., 2-for-1 cocktails on Thursdays).
    """
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="offers")
    event = models.ForeignKey(Event

