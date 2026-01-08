import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Course
from django.db import connection

def check():
    tables = connection.introspection.table_names()
    print(f"Tables found: {len(tables)}")
    if 'myapp_course' in tables:
        print("Table 'myapp_course' EXISTS.")
        count = Course.objects.count()
        print(f"Course count: {count}")
    else:
        print("Table 'myapp_course' DOES NOT EXIST.")

if __name__ == '__main__':
    check()
