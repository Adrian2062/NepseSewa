from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.backends import ModelBackend
from .forms import RegistrationForm, LoginForm
from .models import CustomUser

class EmailBackend(ModelBackend):
    """Custom authentication backend to allow login with email"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(email=username)
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None


def landing_page(request):
    """Landing page view"""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')


def login_view(request):
    """User login/registration page view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    login_form = LoginForm()
    register_form = RegistrationForm()
    
    if request.method == 'POST':
        if 'login' in request.POST:
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            # Authenticate using email
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid email or password.')
        
        elif 'register' in request.POST:
            register_form = RegistrationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('home')
            else:
                for field, errors in register_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
    
    context = {
        'login_form': login_form,
        'register_form': register_form
    }
    return render(request, 'login.html', context)


@login_required(login_url='login')
def home_view(request):
    """Home page view - requires authentication"""
    context = {
        'user': request.user,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'virtual_balance': request.user.virtual_balance,
        'portfolio_value': request.user.portfolio_value,
    }
    return render(request, 'home.html', context)


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing')