from django import forms
from django.contrib.auth.models import User

from .models import Event, EventOccurrence, Venue, Choices 
from django.core.validators import MinValueValidator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UserForm(UserCreationForm):
    """
    A custom form for user registration that includes an email field
    and custom validation for password confirmation.
    """
    email = forms.EmailField(
        required=True, 
        label="Email Address",
        # Adding a placeholder to match the template's style
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )

    class Meta:
        model = User
        # The fields for the base UserCreationForm are 'password1' and 'password2'
        fields = ("username", "email", "password1", "password2") # <-- CORRECTED
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Password'}), # Corrected widget key
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        }

    def clean_email(self):
        """
        Ensure the email is unique, as UserCreationForm doesn't enforce this by default.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean(self):
        """
        Custom validation to check if password and password2 match,
        after base UserCreationForm validation has run.
        """
        cleaned_data = super().clean() 
        
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError(
                "The two password fields didn't match.",
                code='password_mismatch'
            )

        return cleaned_data

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