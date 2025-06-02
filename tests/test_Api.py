# test_api.py
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_api_endpoints():
    """Test all API endpoints"""
    
    print("🧪 Testing Flask API Endpoints...")
    print("=" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()['message']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test 2: Get restaurants
    try:
        response = requests.get(f"{BASE_URL}/restaurants")
        data = response.json()
        print(f"✅ Get restaurants: {response.status_code} - Found {data['count']} restaurants")
    except Exception as e:
        print(f"❌ Get restaurants failed: {e}")
    
    # Test 3: Filter restaurants by cuisine
    try:
        response = requests.get(f"{BASE_URL}/restaurants?cuisine=Italian")
        data = response.json()
        print(f"✅ Filter by cuisine: {response.status_code} - Found {data['count']} Italian restaurants")
    except Exception as e:
        print(f"❌ Filter by cuisine failed: {e}")
    
    # Test 4: Get recommendations
    try:
        response = requests.get(f"{BASE_URL}/recommendations?cuisine=Italian&budget=moderate")
        data = response.json()
        print(f"✅ Get recommendations: {response.status_code} - Found {data['count']} recommendations")
    except Exception as e:
        print(f"❌ Get recommendations failed: {e}")
    
    print("\n🎉 API testing completed!")

if __name__ == "__main__":
    test_api_endpoints()
