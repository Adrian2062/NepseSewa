import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core import mail

def diagnostic():
    email = 'adrianpoudyal@gmail.com'
    User = get_user_model()
    
    with open('trace_output.txt', 'w') as f:
        f.write(f"--- Diagnostic for {email} ---\n")
        
        # Check user count
        users_all = User.objects.filter(email__iexact=email)
        f.write(f"Total users found with this email: {users_all.count()}\n")
        
        for u in users_all:
            f.write(f"User ID: {u.id}\n")
            f.write(f"Is Active: {u.is_active}\n")
            f.write(f"Has Usable Password: {u.has_usable_password()}\n")
            f.write(f"Last Login: {u.last_login}\n")
        
        # Simulate PasswordResetForm.get_users (internal logic)
        active_users = User._default_manager.filter(**{
            '%s__iexact' % User.get_email_field_name(): email,
            'is_active': True,
        })
        f.write(f"Active users filtering by Django logic: {active_users.count()}\n")
        
        # Try to validate and save the form
        form = PasswordResetForm(data={'email': email})
        if form.is_valid():
            f.write("Form is valid.\n")
            form.save(
                use_https=False,
                from_email='support@nepsesewa.com',
                email_template_name='auth/password_reset_email.txt',
                subject_template_name='auth/password_reset_subject.txt'
            )
            f.write("form.save() executed.\n")
            f.write(f"Emails in outbox: {len(mail.outbox)}\n")
            if mail.outbox:
                f.write(f"Subject: {mail.outbox[0].subject}\n")
                f.write(f"To: {mail.outbox[0].to}\n")
        else:
            f.write(f"Form errors: {form.errors}\n")

if __name__ == "__main__":
    diagnostic()
