import os
import django
import json
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.views import api_get_recommendations, api_refresh_recommendation
from myapp.models import Watchlist, NEPSEPrice, StockRecommendation

def test_watchlist_api():
    print("--- Starting Watchlist API Test ---")
    User = get_user_model()
    
    # Get or create a test user
    username = 'testuser'
    email = 'test@example.com'
    
    # Try finding by username first
    user = User.objects.filter(username=username).first()
    if not user:
        # Try finding by email
        user = User.objects.filter(email=email).first()
        
    if not user:
        # Create new if neither exists
        try:
            user = User.objects.create_user(username=username, email=email, password='password123')
            print(f"Created test user: {username}")
        except Exception as e:
            # Fallback: just get the first superuser or any user to run the test
            print(f"Could not create test user: {e}")
            user = User.objects.first()
            print(f"Falling back to existing user: {user.username}")
    else:
        print(f"Using existing test user: {user.username}")

    # Ensure watchlist has at least one item
    symbol = 'NABIL'
    Watchlist.objects.get_or_create(user=user, symbol=symbol)
    print(f"Ensured {symbol} is in watchlist.")

    # Mock Request
    factory = RequestFactory()
    
    # Test 1: Get Recommendations
    print("\n[TEST 1] Testing api_get_recommendations...")
    request = factory.get('/api/recommendations/')
    request.user = user
    
    response = api_get_recommendations(request)
    print(f"Status Code: {response.status_code}")
    
    content = json.loads(response.content)
    if content.get('success'):
        print("SUCCESS: Fetched recommendations.")
        print(f"Data: {content['data'][:1]}") # Print first item
    else:
        print(f"FAILURE: {content.get('message')}")
        print(f"Full Response: {content}")

    # Test 2: Refresh Recommendation (Simulate)
    print("\n[TEST 2] Testing api_refresh_recommendation (Mock)...")
    # Note: validation logic in view might fail if ML libraries are missing or no data
    # We just want to ensure it handles errors gracefully and doesn't crash 500
    
    # Create request
    data = {'symbol': symbol}
    request_post = factory.post(
        '/api/recommendations/refresh/', 
        data=json.dumps(data), 
        content_type='application/json'
    )
    request_post.user = user
    
    response_refresh = api_refresh_recommendation(request_post)
    print(f"Status Code: {response_refresh.status_code}")
    
    content_refresh = json.loads(response_refresh.content)
    if content_refresh.get('success'):
        print(f"SUCCESS: Refreshed recommendation for {symbol}.")
        print(f"Data: {content_refresh['data']}")
    else:
        # Expected if no data or ML missing, but status code should be 200 (handled error)
        # or 500 if we explicitly returned 500 for unhandled exceptions (which we actully catch now)
        print(f"HANDLED FAILURE: {content_refresh.get('message')}")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    test_watchlist_api()
