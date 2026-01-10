import time
from django.utils import timezone
from myapp.models import NEPSEPrice
from myapp.views import api_available_dates
from django.test import RequestFactory

def run_check():
    print(f"Checking NEPSEPrice count at {timezone.now()}...")
    count = NEPSEPrice.objects.count()
    print(f"Total NEPSEPrice records: {count}")
    
    if count == 0:
        print("WARNING: Table is empty.")
        return

    print("Benchmarking api_available_dates...")
    factory = RequestFactory()
    request = factory.get('/api/available-dates/')
    
    start = time.time()
    response = api_available_dates(request)
    end = time.time()
    
    print(f"api_available_dates took {end - start:.4f} seconds")
    print(f"Response status: {response.status_code}")
    print(f"Response content prefix: {response.content[:100]}")

if __name__ == "__main__":
    run_check()
