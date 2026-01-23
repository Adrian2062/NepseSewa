from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John',
            'id': 'register-firstname'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Doe',
            'id': 'register-lastname'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'john@example.com',
            'id': 'register-email'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
            'id': 'register-password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'register-confirm-password'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'john@example.com',
            'id': 'login-email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'login-password'
        })
    )


# ============= SETTINGS FORMS =============

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'soft-input w-100',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'soft-input w-100',
                'placeholder': 'Last name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'soft-input w-100',
                'placeholder': '98XXXXXXXX'
            }),
        }
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError('First name is required.')
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise forms.ValidationError('Last name is required.')
        return last_name


class EmailUpdateForm(forms.Form):
    """Form for updating user email"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'soft-input w-100',
            'placeholder': 'Email'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('This email is already in use by another account.')
        return email


class PasswordChangeCustomForm(forms.Form):
    """Form for changing user password"""
    current_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'soft-input w-100',
            'placeholder': '••••••••'
        })
    )
    new_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'soft-input w-100',
            'placeholder': 'New password'
        })
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'soft-input w-100',
            'placeholder': 'Confirm new password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError('Current password is incorrect.')
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError('New passwords do not match.')
        
        return cleaned_data


class NotificationPreferenceForm(forms.ModelForm):
    """Form for updating notification preferences"""
    class Meta:
        model = CustomUser
        fields = ['buy_sell_notifications']
        widgets = {
            'buy_sell_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input switch'
            })
        }
