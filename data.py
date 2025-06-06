import os
from supabase import create_client
import uuid
from faker import Faker
from dotenv import load_dotenv

load_dotenv()

# Use SERVICE_ROLE key instead of ANON key for data seeding
supabase = create_client(
    os.getenv('SUPABASE_URL'), 
    os.getenv('SUPABASE_ANON_KEY')  # This bypasses RLS
)

fake = Faker()

cuisines = ['Italian', 'Mexican', 'Chinese', 'Japanese', 'American', 
            'French', 'Thai', 'Indian', 'Mediterranean', 'Vietnamese']
cities = [fake.city() for _ in range(25)]

for _ in range(100):
    restaurant = {
        'name': fake.company(),
        'cuisine': fake.random_element(cuisines),
        'location': fake.street_address(),
        'city': fake.random_element(cities),
        'capacity': fake.random_int(20, 200),
        'price_range': fake.random_element(['$', '$$', '$$$', '$$$$']),
        'rating': round(max(0, min(5, fake.pyfloat(min_value=0, max_value=5))), 1)
    }
    supabase.table('restaurants').insert(restaurant).execute()