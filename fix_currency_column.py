import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

with connection.cursor() as cursor:
    try:
        cursor.execute("ALTER TABLE users DROP COLUMN default_currency CASCADE")
        print("Column 'default_currency' dropped successfully from 'users' table.")
    except Exception as e:
        print(f"Error: {e}")
