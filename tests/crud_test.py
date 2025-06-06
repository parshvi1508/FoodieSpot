from supabase import create_client
import os

supabase = create_client(os.getenv('SUPABASE_URL'),
                        os.getenv('SUPABASE_ANON_KEY'))

# Create
new_rest = supabase.table('restaurants').insert({
    'name': 'Test Restaurant',
    'cuisine': 'Test',
    'location': '123 Test St',
    'city': 'Testville',
    'capacity': 50,
    'price_range': '$$',
    'rating': 4.5
}).execute()

# Read
restaurants = supabase.table('restaurants').select('*').execute()
print(f"Found {len(restaurants.data)} restaurants")

# Update
supabase.table('restaurants').update({'capacity': 60}).eq('id', new_rest.data[0]['id']).execute()

# Delete
supabase.table('restaurants').delete().eq('id', new_rest.data[0]['id']).execute()