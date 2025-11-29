from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def index(request):
    """Landing page view"""
    return render(request, 'landing.html')

def login_view(request):
    """Handle login and registration"""
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'login':
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Login successful!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
                
        elif form_type == 'register':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
            else:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name
                )
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')
    
    # Always render login page at the end, either for GET or if POST fails
    return render(request, 'login.html')
    """Handle login and registration"""
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'login':
            # Handle login
            email = request.POST.get('email')
            password = request.POST.get('password')
            remember_me = request.POST.get('remember_me')
            
            # Since we're using email as username for simplicity
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Login successful!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
                
        elif form_type == 'register':
            # Handle registration
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            # Basic validation
            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
            else:
                # Create user (using email as username for simplicity)
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name
                )
                messages.success(request, 'Account created successfully! Please login.')
                # Directly render login.html
                return render(request, 'login.html')


def password_reset(request):
    if request.method == 'POST':
        # handle password reset logic here
        email = request.POST.get('email')
        # For now, just redirect to login
        return render(request, 'login.html', {'message': 'Password reset link sent!'})
    return render(request, 'password_reset.html')

@login_required
def dashboard(request):
    """Dashboard view for logged-in users"""
    return render(request, 'dashboard.html')

@login_required
def portfolio(request):
    """Portfolio view"""
    return render(request, 'portfolio.html')

@login_required
def trade(request):
    """Trade view"""
    return render(request, 'trade.html')

@login_required
def market(request):
    """Market view"""
    return render(request, 'market.html')

@login_required
def watchlist(request):
    """Watchlist view"""
    return render(request, 'watchlist.html')

@login_required
def learn(request):
    """Learning resources view"""
    return render(request, 'learn.html')

@login_required
def settings(request):
    """Settings view"""
    return render(request, 'settings.html')

def logout_view(request):
    """Handle logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')