import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Sector, Stock
import re

# 1. Find and delete all numeric sector names
numeric_pattern = re.compile(r'^[\d,.\s]+$')
bad_sectors = Sector.objects.all()
deleted = 0
for sec in bad_sectors:
    if numeric_pattern.match(sec.name.strip()):
        print(f"Deleting bad sector: '{sec.name}'")
        # Before deleting, move stocks that belong to it to null
        Stock.objects.filter(sector=sec).update(sector=None)
        sec.delete()
        deleted += 1

print(f"\nDeleted {deleted} invalid numeric sectors.")

# 2. Create the 14 correct sector names
CORRECT_SECTORS = [
    "Commercial Banks",
    "Development Banks",
    "Microfinance",
    "Finance",
    "Investment",
    "Hotels & Tourism",
    "Manufacturing & Processing",
    "Others",
    "Hydropower",
    "Life Insurance",
    "Non-Life Insurance",
    "Mutual Fund",
    "Corporate Debentures",
    "Trading",
]

created = 0
for name in CORRECT_SECTORS:
    sector, was_created = Sector.objects.get_or_create(name=name)
    if was_created:
        print(f"Created sector: {name}")
        created += 1
    else:
        print(f"Already exists: {name}")

print(f"\nDone! Created {created} new sectors. Total: {Sector.objects.count()} sectors.")
print("\nFinal sector list:")
for s in Sector.objects.all().order_by('name'):
    print(f"  - {s.name}")
