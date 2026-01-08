
import os
import django
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "NepseSewa.settings")
django.setup()

print("Checking database schema...")
with connection.cursor() as cursor:
    try:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'myapp_course';")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Columns in myapp_course: {columns}")
        if 'slug' in columns:
            print("SUCCESS: Slug column found.")
        else:
            print("FAILURE: Slug column missing.")
    except Exception as e:
        print(f"Error: {e}")
