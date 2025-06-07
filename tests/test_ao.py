# test_tools.py
from ai_agent import RestaurantAI

def test_individual_tools():
    """Test each tool function individually"""
    
    try:
        ai_agent = RestaurantAI()
        
        # Test 1: Search restaurants tool
        print("=== Testing Search Restaurants Tool ===")
        search_params = {
            'cuisine': 'Italian',
            'city': 'Philadelphia'
        }
        search_result = ai_agent._process_tool_search_restaurants(search_params)
        print(f"Search Result: {search_result}")
        
        # Test 2: Create reservation tool
        print("\n=== Testing Create Reservation Tool ===")
        reservation_params = {
            'restaurant_name': 'Amalfi Coast Cafe',
            'customer_name': 'Test User 03',
            'customer_email': 'test3@example.com',
            'party_size': 6,
            'reservation_date': '2025-06-08',
            'reservation_time': '19:00'
        }
        reservation_result = ai_agent._process_tool_create_reservation(reservation_params)
        print(f"Reservation Result: {reservation_result}")
        
        # Test 3: Check availability tool
        print("\n=== Testing Check Availability Tool ===")
        availability_params = {
            'restaurant_name': 'Amalfi Coast Cafe',
            'date': '2025-06-08',
            'time': '19:00',
            'party_size': 2
        }
        availability_result = ai_agent._process_tool_check_availability(availability_params)
        print(f"Availability Result: {availability_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool testing failed: {e}")
        return False

if __name__ == "__main__":
    test_individual_tools()
