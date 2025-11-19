from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Feedback
from django.utils.translation import gettext_lazy as _

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text='Required. Inform a valid email address.'
    )
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    company = forms.CharField(max_length=100, required=False)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput,
        strip=False,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email', 'company')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        css_class = 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm'
        # The fields dictionary includes the fields from the form and the inherited ones
        self.fields['password1'].widget.attrs.update({'class': css_class})
        self.fields['password2'].widget.attrs.update({'class': css_class})
        self.fields['email'].widget.attrs.update({'class': css_class})
        self.fields['first_name'].widget.attrs.update({'class': css_class})
        self.fields['last_name'].widget.attrs.update({'class': css_class})
        self.fields['company'].widget.attrs.update({'class': css_class})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Vartotojas su tokiu el. pašto adresu jau egzistuoja.")
        return email

    def save(self, commit=True):
        self.instance.username = self.cleaned_data["email"]
        user = super().save(commit=commit)
        return user

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            'rating', 
            'teamwork_rating', 
            'communication_rating', 
            'initiative_rating', 
            'technical_skills_rating', 
            'problem_solving_rating',
            'keywords', 
            'comments',
            'feedback'
        ]