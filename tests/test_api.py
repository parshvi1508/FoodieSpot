import pytest
import json
import logging
from datetime import date, timedelta
from app import app

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        logger.info("Test client initialized")
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

def test_get_restaurants(client):
    """Test getting all restaurants"""
    response = client.get('/api/restaurants')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert isinstance(data['data'], list)

def test_availability_check_invalid_date(client):
    """Test availability check with past date"""
    availability_data = {
        "restaurant_id": "test-id",
        "date": "2020-01-01",
        "time": "19:00",
        "party_size": 2
    }
    
    response = client.post('/api/availability', 
                          data=json.dumps(availability_data),
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False

def test_create_reservation_valid(client):
    """Test creating a valid reservation"""
    # Get test restaurant ID
    restaurants_response = client.get('/api/restaurants')
    restaurants_data = json.loads(restaurants_response.data)
    
    if not restaurants_data['data']:
        pytest.skip("No restaurants available for testing")
    
    restaurant_id = restaurants_data['data'][0]['id']
    
    reservation_data = {
        "restaurant_id": restaurant_id,
        "date": (date.today() + timedelta(days=2)).isoformat(),
        "time": "20:00",
        "party_size": 2,
        "user_email": "test@example.com",
        "user_name": "Test User"
    }
    
    response = client.post('/api/reservations', 
                          data=json.dumps(reservation_data),
                          content_type='application/json')
    
    # Allow for success (201) or conflict (409)
    assert response.status_code in [201, 409]

def test_create_reservation_invalid_email(client):
    """Test creating reservation with invalid email"""
    reservation_data = {
        "restaurant_id": "test-id",
        "date": (date.today() + timedelta(days=1)).isoformat(),
        "time": "19:00",
        "party_size": 2,
        "user_email": "invalid-email",
        "user_name": "Test User"
    }
    
    response = client.post('/api/reservations', 
                          data=json.dumps(reservation_data),
                          content_type='application/json')
    assert response.status_code == 400

def test_404_endpoint(client):
    """Test 404 error handling"""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404

if __name__ == '__main__':
    pytest.main([__file__])
