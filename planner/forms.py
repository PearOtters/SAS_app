from django import forms
from django.contrib.auth.models import User

from .models import Event, EventOccurrence, Venue, Choices 
from django.core.validators import MinValueValidator

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password',)

class EventCreationForm(forms.Form):
    """
    Updated form structure to reflect the removal of Venue and the requirement
    of explicit location coordinates and name.
    """
    
    # Event Fields
    eventName = forms.CharField(max_length=200, label="Event Name")
    eventDescription = forms.CharField(widget=forms.Textarea, required=False, label="Description")
    
    # EventOccurrence Fields
    selected_date = forms.DateField(widget=forms.HiddenInput(), required=True)
    eventTime = forms.TimeField(label="Start Time")
    eventDuration = forms.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        required=False, 
        label="Duration (hours)",
        validators=[MinValueValidator(0.5)]
    )
    eventAttendees = forms.IntegerField(min_value=1, required=False, label="Expected Attendees")

    # LOCATION FIELDS (Updated to be mandatory for creation)
    selectedLat = forms.DecimalField(max_digits=9, decimal_places=6, required=True, widget=forms.HiddenInput())
    selectedLng = forms.DecimalField(max_digits=9, decimal_places=6, required=True, widget=forms.HiddenInput())
    locationName = forms.CharField(max_length=255, required=False, widget=forms.HiddenInput())
    
    # Removed selectedVenueId
    
    # Custom clean method is now simple or can be removed
    def clean(self):
        cleaned_data = super().clean()
        # No more Venue validation needed here
        return cleaned_data