# Test script to verify data
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

# Test queries
total = supabase.table('restaurants').select('id', count='exact').execute()
print(f"Total restaurants: {total.count}")

italian = supabase.table('restaurants').select('name, city, rating').eq('cuisine', 'Italian').limit(5).execute()
print(f"\nSample Italian restaurants:")
for r in italian.data:
    print(f"- {r['name']} - {r['city']} - {r['rating']}⭐")
