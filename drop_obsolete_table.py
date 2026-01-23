import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

with connection.cursor() as cursor:
    cursor.execute("DROP TABLE IF EXISTS user_preferences CASCADE")
    print("Table 'user_preferences' dropped successfully.")
