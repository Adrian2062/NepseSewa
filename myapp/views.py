from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .forms import RegistrationForm

User = get_user_model()

# --- Email authentication backend ---
class EmailBackend(ModelBackend):
    """
    Authenticate using email instead of username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email', username)
        if email is None or password is None:
            return None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

# --- Views ---
def landing_page(request):
    return render(request, 'landing.html')


def login_view(request):
    if request.method == 'POST':
        form_type = request.POST.get('form-type')
        if form_type == 'login':
            email = request.POST.get('email')
            password = request.POST.get('password')

            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')

            messages.error(request, "Invalid email or password")
            return redirect('login')

        # REGISTER
        elif form_type == 'register':
            form = RegistrationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Account created successfully! Please login.")
                return redirect('login')
            return render(request, 'login.html', {'form': form})

    return render(request, 'login.html')


def password_reset(request):
    if request.method == "POST":
        messages.success(request, "Password reset link sent!")
        return redirect("login")

    return render(request, "password_reset.html")


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def portfolio(request):
    return render(request, 'portfolio.html')

@login_required
def trade(request):
    return render(request, 'trade.html')

@login_required
def market(request):
    return render(request, 'market.html')

@login_required
def watchlist(request):
    return render(request, 'watchlist.html')

@login_required
def learn(request):
    return render(request, 'learn.html')

@login_required
def settings_view(request):
    return render(request, 'settings.html')


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('landing')
