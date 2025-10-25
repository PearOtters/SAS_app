# nightout/models.py
from __future__ import annotations

from django.db import models
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
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="offers")
    title = models.CharField(max_length=160)
    details = models.TextField(blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    days_of_week = models.CharField(
        max_length=30,
        blank=True,
        help_text="CSV of weekday numbers 0=Mon .. 6=Sun (e.g., '3,4' for Thu+Fri).",
    )
    budget_improvement = models.SmallIntegerField(
        default=0,
        help_text="Negative numbers mean cheaper (improves affordability)."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_active", "title"]


# ---------- Data Provenance ----------

class DataSource(models.Model):
    """
    Tracks where a Venue/Event/Offer came from (hardcoded, scraper, API).
    """
    source_type = models.CharField(max_length=20, choices=DataSourceType.choices)
    provider = models.CharField(max_length=120, help_text="e.g., 'Manual seed', 'Eventbrite', 'Songkick'")
    source_url = models.URLField(blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)

    # Generic relation via IDs (kept simple & portable)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, null=True, blank=True, related_name="sources")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name="sources")
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, null=True, blank=True, related_name="sources")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["source_type", "provider"])]
        ordering = ["-last_checked", "-created_at"]

    def __str__(self) -> str:
        target = self.venue or self.event or self.offer
        return f"{self.get_source_type_display()}:{self.provider} -> {target}"


# ---------- Lightweight “user” signals (no auth required) ----------

class Thumb(models.Model):
    """
    Simple up/down votes to crowdsource popularity without full auth.
    """
    UP = 1
    DOWN = -1
    VOTE_CHOICES = ((UP, "Up"), (DOWN, "Down"))

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="thumbs")
    voter_name = models.CharField(max_length=80, blank=True, help_text="Optional display name")
    vote = models.SmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["event", "vote"])]

    def __str__(self) -> str:
        return f"{'👍' if self.vote == 1 else '👎'} {self.event}"


# ---------- Recommendation Engine ----------

class RecoWeights(models.Model):
    """
    Tunable weights for the Office Fun Score.
    Keep only a small number of rows (e.g., 'default', 'budget_friendly', etc.).
    """
    name = models.CharField(max_length=50, unique=True, default="default")

    w_kind_match = models.FloatField(default=1.0)          # activity kind matches requested
    w_budget_fit = models.FloatField(default=0.8)          # budget band vs requested
    w_group_fit = models.FloatField(default=0.8)           # within min/max group
    w_occasion_bonus = models.FloatField(default=0.5)      # suits occasion (e.g., karaoke for farewell)
    w_popularity = models.FloatField(default=0.6)          # thumbs & ratings
    w_recency = models.FloatField(default=0.4)             # upcoming soon
    w_offer = models.FloatField(default=0.3)               # active offers

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Reco Weights: {self.name}"


class RecommendationQuery(models.Model):
    """
    A single user request we can re-run or audit later.
    Produces up to Top-5 RecommendationResult rows.
    """
    for_date = models.DateField(help_text="Intended night out date")
    group_size = models.PositiveIntegerField(default=6)
    mood = models.CharField(max_length=60, blank=True, help_text="Free text: 'chill', 'competitive', 'party'")
    budget = models.CharField(max_length=10, choices=BudgetBand.choices, default=BudgetBand.MEDIUM)
    occasion = models.CharField(max_length=20, choices=Occasion.choices, default=Occasion.NONE)
    preferred_kinds = models.CharField(
        max_length=120,
        blank=True,
        help_text="CSV of ActivityKind values to prefer (e.g., 'BAR,KARAOKE')."
    )
    weights = models.ForeignKey(RecoWeights, on_delete=models.SET_NULL, null=True, blank=True)

    created_by = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["for_date"])]

    def __str__(self) -> str:
        return f"Reco for {self.for_date} (size {self.group_size}, {self.get_budget_display()})"


class RecommendationResult(models.Model):
    """
    One scored item in the Top-N list for a query.
    It can point to an Event (preferred) or fall back to a Venue when no dated event is needed.
    """
    query = models.ForeignKey(RecommendationQuery, on_delete=models.CASCADE, related_name="results")
    rank = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    office_fun_score = models.DecimalField(max_digits=5, decimal_places=2)

    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="recommendations")
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name="recommendations")

    reason = models.TextField(
        blank=True,
        help_text="Short rationale shown to users (e.g., 'Fits budget, has Thursday quiz, walkable from office')."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rank"]
        unique_together = [("query", "rank")]

    def __str__(self) -> str:
        target = self.event or self.venue
        return f"#{self.rank} {target} — {self.office_fun_score}"


# ---------- Convenience scoring helpers (purely optional) ----------

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def popularity_signal(event: Event) -> float:
    """
    Blend rating and thumbs into 0..1.
    """
    # Normalise average rating (0..5) to 0..1
    rating_part = float(event.avg_rating) / 5.0 if event.avg_rating else 0.0
    # Thumbs up minus down, scaled
    up = event.thumbs.filter(vote=Thumb.UP).count()
    down = event.thumbs.filter(vote=Thumb.DOWN).count()
    thumb_part = 0.5 + 0.5 * clamp01((up - down) / max(1.0, up + down))
    return clamp01(0.6 * rating_part + 0.4 * thumb_part)


def basic_office_fun_score(
    *,
    event: Event,
    query: RecommendationQuery,
    weights: RecoWeights | None = None,
) -> float:
    """
    A simple, explainable scorer you can call from a service layer or management command.
    Not used automatically by models; included here to document the intended scoring.
    """
    w = weights or query.weights or RecoWeights.objects.filter(name="default").first()
    # If no weights exist yet, use sensible defaults
    if not w:
        w = RecoWeights(
            name="__ephemeral__",
            w_kind_match=1.0, w_budget_fit=0.8, w_group_fit=0.8,
            w_occasion_bonus=0.5, w_popularity=0.6, w_recency=0.4, w_offer=0.3
        )

    # Signals in 0..1
    kind_pref = set([k.strip().upper() for k in (query.preferred_kinds or "").split(",") if k.strip()])
    s_kind = 1.0 if (event.kind in kind_pref or not kind_pref) else 0.6

    s_budget = 1.0 if event.budget == query.budget else (0.7 if query.budget == BudgetBand.MEDIUM else 0.5)

    s_group = 1.0 if event.fits_group(query.group_size) else 0.0

    # Occasion heuristics
    occasion_bonus_map = {
        Occasion.RETIREMENT: {ActivityKind.KARAOKE, ActivityKind.BAR, ActivityKind.LIVE_MUSIC},
        Occasion.CHRISTMAS: {ActivityKind.LIVE_MUSIC, ActivityKind.FOOD, ActivityKind.TRIVIA},
        Occasion.BIRTHDAY: {ActivityKind.KARAOKE, ActivityKind.BAR, ActivityKind.FOOD},
    }
    preferred_for_occ = occasion_bonus_map.get(Occasion(query.occasion), set())
    s_occasion = 1.0 if event.kind in preferred_for_occ else 0.6 if query.occasion != Occasion.NONE else 0.8

    # Near-date boost (closer to query date is better)
    days_diff = abs((event.start.date() - query.for_date).days) if event.start else 14
    s_recency = clamp01(1.0 - (days_diff / 21.0))  # within ~3 weeks

    # Offer present?
    s_offer = 1.0 if event.offers.filter(is_active=True).exists() else 0.0

    s_pop = popularity_signal(event)

    score = (
        w.w_kind_match * s_kind
        + w.w_budget_fit * s_budget
        + w.w_group_fit * s_group
        + w.w_occasion_bonus * s_occasion
        + w.w_recency * s_recency
        + w.w_offer * s_offer
        + w.w_popularity * s_pop
    )

    # Normalise to 0..100 for pleasant display
    return round(100.0 * clamp01(score / (w.w_kind_match + w.w_budget_fit + w.w_group_fit +
                                          w.w_occasion_bonus + w.w_recency + w.w_offer + w.w_popularity)), 2)
