import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print("--- REGISTERED USERS ---")
for u in User.objects.all():
    print(f"ID: {u.id} | Email: '{u.email}' | Username: '{u.username}' | Active: {u.is_active}")
print("------------------------")

from django.core.mail import send_mail
try:
    print("Attempting to send test email to file...")
    send_mail(
        'Test Subject',
        'Test Body',
        'test@example.com',
        ['test@example.com'],
        fail_silently=False,
    )
    print("Test email command executed.")
except Exception as e:
    print(f"Test email failed: {e}")
