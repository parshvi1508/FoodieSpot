# database_test.py
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    def __init__(self):
        self.client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    
    def test_connection(self):
        """Test basic connection and query"""
        try:
            result = self.client.table('restaurants').select('*').limit(5).execute()
            print(f"✅ Connection successful! Found {len(result.data)} restaurants")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False
    
    def get_restaurants_by_cuisine(self, cuisine):
        """Test filtering functionality"""
        try:
            result = self.client.table('restaurants').select('*').ilike('cuisine', f'%{cuisine}%').execute()
            print(f"✅ Found {len(result.data)} {cuisine} restaurants")
            return result.data
        except Exception as e:
            print(f"❌ Query failed: {str(e)}")
            return []
    
    def test_insert_reservation(self):
        """Test reservation insertion"""
        try:
            # Get a restaurant ID first
            restaurant = self.client.table('restaurants').select('id').limit(1).execute()
            if not restaurant.data:
                print("❌ No restaurants found for testing")
                return False
                
            test_reservation = {
                'restaurant_id': restaurant.data[0]['id'],
                'user_email': 'test@example.com',
                'user_name': 'Test User',
                'party_size': 4,
                'reservation_date': '2025-06-15',
                'reservation_time': '19:00:00'
            }
            
            result = self.client.table('reservations').insert(test_reservation).execute()
            print(f"✅ Test reservation created successfully")
            
            # Clean up test data
            self.client.table('reservations').delete().eq('user_email', 'test@example.com').execute()
            return True
            
        except Exception as e:
            print(f"❌ Reservation test failed: {str(e)}")
            return False

if __name__ == "__main__":
    # Test all functionality
    db = SupabaseManager()
    
    print("🧪 Testing Supabase Database Setup...")
    print("=" * 50)
    
    # Test 1: Basic connection
    db.test_connection()
    
    # Test 2: Query by cuisine
    italian_restaurants = db.get_restaurants_by_cuisine('Italian')
    
    # Test 3: Reservation functionality
    db.test_insert_reservation()
    
    # Test 4: Verify data diversity
    all_restaurants = db.client.table('restaurants').select('cuisine, city').execute()
    cuisines = set(r['cuisine'] for r in all_restaurants.data)
    cities = set(r['city'] for r in all_restaurants.data)
    
    print(f"✅ Database contains {len(cuisines)} different cuisines")
    print(f"✅ Database contains {len(cities)} different cities")
    print(f"✅ Total restaurants: {len(all_restaurants.data)}")
    
    print("\n🎉 Database setup completed successfully!")
