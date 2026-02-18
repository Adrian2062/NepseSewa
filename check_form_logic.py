import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

def check_form_logic():
    email = 'adrianpoudyal@gmail.com'
    UserModel = get_user_model()
    
    with open('form_debug.txt', 'w') as f:
        f.write(f"--- Form Logic Debug for {email} ---\n")
        
        # 1. How Django filters users in PasswordResetForm
        users = list(UserModel._default_manager.filter(email__iexact=email, is_active=True))
        f.write(f"Found {len(users)} active users with this email.\n")
        
        for user in users:
            f.write(f"User PK: {user.pk}\n")
            f.write(f"Is Active: {user.is_active}\n")
            f.write(f"Has Usable Password: {user.has_usable_password()}\n")
            
            # Form-specific check: if has_usable_password() returns False, form skips it
            if not user.has_usable_password():
                f.write("WARNING: Django will SKIP this user because password is not usable (Social Login user?)\n")
        
        # 2. Try to actually send if valid
        form = PasswordResetForm(data={'email': email})
        if form.is_valid():
            f.write("Form is valid.\n")
            # We already know SMTP works from previous tests, but let's see if this specific call fails
            try:
                # We'll mock the actual email sending to see if context generation works
                # but if we want to confirm the link exists, we'll let it try to send
                form.save(
                    use_https=False,
                    email_template_name='auth/password_reset_email.txt',
                    subject_template_name='auth/password_reset_subject.txt'
                )
                f.write("form.save() called successfully.\n")
            except Exception as e:
                f.write(f"EXCEPTION playing form.save(): {str(e)}\n")
        else:
            f.write(f"Form NOT valid: {form.errors}\n")

if __name__ == "__main__":
    check_form_logic()
