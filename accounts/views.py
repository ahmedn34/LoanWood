from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserSignupForm, UserLoginForm, ProfileUpdateForm
from .services import get_reputation_stats


def signup_view(request):
    """Handles new user registration and profile creation."""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = UserSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Loanwood, {user.username}! Your community profile is ready.")
            return redirect('core:home')
    else:
        form = UserSignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    """Custom authentication login view."""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next') or 'core:home'
                return redirect(next_url)
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Django 5+ compatible logout view handling POST requests."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been safely logged out.")
        return redirect('core:home')
    return redirect('core:home')


def profile_view(request, username=None):
    """Displays user profile, listed items, and community reputation stats."""
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        profile_user = request.user

    stats = get_reputation_stats(profile_user)
    items = profile_user.items.filter(is_deleted=False)

    return render(request, 'accounts/profile.html', {
        'profile_user': profile_user,
        'stats': stats,
        'items': items,
        'is_own_profile': request.user == profile_user,
    })


@login_required
def profile_edit_view(request):
    """Enables members to edit their bio, neighborhood, and avatar."""
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})
