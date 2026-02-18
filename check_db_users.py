import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import CustomUser

def check_users():
    target_email = 'adrianpoudyal@gmail.com'
    users = CustomUser.objects.filter(email=target_email)
    
    with open('db_check.txt', 'w') as f:
        f.write(f"--- Database Check for {target_email} ---\n")
        if not users.exists():
            f.write(f"ERROR: No user found with email {target_email}\n")
            f.write("All registered users in DB:\n")
            for u in CustomUser.objects.all():
                f.write(f"- {u.email} (Active: {u.is_active})\n")
        else:
            for u in users:
                f.write(f"FOUND: {u.username} | {u.email} | Active: {u.is_active} | Has Password: {u.has_usable_password()}\n")

if __name__ == "__main__":
    check_users()
