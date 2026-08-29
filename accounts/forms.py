from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile


class UserSignupForm(UserCreationForm):
    """Registration form creating both User credentials and Profile attributes."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
            'autocomplete': 'email'
        })
    )
    neighborhood = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Oakwood District, North Hills'
        })
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Tell neighbors a bit about your DIY projects and skills...'
        })
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'neighborhood', 'bio', 'avatar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a unique username'
        })
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = user.profile
            profile.neighborhood = self.cleaned_data.get('neighborhood', '')
            profile.bio = self.cleaned_data.get('bio', '')
            if self.cleaned_data.get('avatar'):
                profile.avatar = self.cleaned_data['avatar']
            profile.save()
        return user


class UserLoginForm(AuthenticationForm):
    """Custom styled authentication login form."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username or email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    """Form allowing members to update neighborhood location, bio, and avatar."""
    class Meta:
        model = Profile
        fields = ['neighborhood', 'bio', 'avatar']
        widgets = {
            'neighborhood': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Maplewood Ridge'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your woodworking, mechanics, or gardening interests...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control-file'
            })
        }
