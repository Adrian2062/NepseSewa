import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Course
from django.db import connection

def check():
    with open('db_status.txt', 'w') as f:
        try:
            tables = connection.introspection.table_names()
            f.write(f"Tables found: {len(tables)}\n")
            if 'myapp_course' in tables:
                f.write("Table 'myapp_course' EXISTS.\n")
                count = Course.objects.count()
                f.write(f"Course count: {count}\n")
            else:
                f.write("Table 'myapp_course' DOES NOT EXIST.\n")
        except Exception as e:
            f.write(f"Error checking DB: {str(e)}\n")

if __name__ == '__main__':
    check()
