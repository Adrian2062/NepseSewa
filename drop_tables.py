
import os
import sys

print("Starting script...")

try:
    import django
    from django.db import connection
    print("Imports successful.")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# Setup Django
print("Setting up Django...")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "NepseSewa.settings")
try:
    django.setup()
    print("Django setup complete.")
except Exception as e:
    print(f"Django Setup Error: {e}")
    sys.exit(1)

def drop_tables():
    tables_to_drop = [
        'myapp_usercourseprogress',
        'myapp_course', 
        'myapp_coursecategory'
    ]
    
    print("Connecting to database...")
    try:
        with connection.cursor() as cursor:
            print("Connected. Dropping tables...")
            for table in tables_to_drop:
                try:
                    # CASCADE is needed to remove dependent foreign keys
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                    print(f"Dropped table {table}")
                except Exception as e:
                    print(f"Error dropping {table}: {e}")
    except Exception as e:
        print(f"Database Connection Error: {e}")

if __name__ == "__main__":
    drop_tables()
    print("Done.")
