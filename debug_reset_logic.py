import os
import django
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

def debug_reset():
    User = get_user_model()
    email = 'adrianpoudyal@gmail.com'
    
    with open('reset_debug.txt', 'w') as f:
        try:
            user = User.objects.get(email=email)
            f.write(f"--- Debugging Reset for {email} ---\n")
            f.write(f"Is Active: {user.is_active}\n")
            f.write(f"Has Usable Password: {user.has_usable_password()}\n")
            
            # Manually trigger the reset form logic
            form = PasswordResetForm(data={'email': email})
            if form.is_valid():
                f.write("Form is valid. Attempting to save (send email)...\n")
                form.save(
                    use_https=False,
                    from_email=None,
                    request=None
                )
                f.write("form.save() completed.\n")
            else:
                f.write(f"Form errors: {form.errors}\n")
        except Exception as e:
            f.write(f"ERROR: {str(e)}\n")

if __name__ == "__main__":
    debug_reset()
