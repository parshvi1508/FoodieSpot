import os
import random
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'), 
    os.getenv('SUPABASE_ANON_KEY')
)

# Proper restaurant names by cuisine type
restaurant_names = {
    'Italian': ['Bella Vista', 'Casa Milano', 'Trattoria Roma', 'Pasta Palace', 'Villa Toscana', 'La Dolce Vita', 'Nonna\'s Kitchen', 'Amalfi Coast', 'Venetian Garden', 'Sicilian Sunset'],
    'Chinese': ['Dragon Palace', 'Golden Wok', 'Jade Garden', 'Bamboo House', 'Great Wall', 'Phoenix Restaurant', 'Lucky Star', 'Mandarin Garden', 'Red Lantern', 'Imperial Kitchen'],
    'Japanese': ['Sakura Sushi', 'Tokyo Bay', 'Zen Garden', 'Sushi Zen', 'Ramen House', 'Kyoto Kitchen', 'Wasabi Grill', 'Ninja Sushi', 'Mount Fuji', 'Osaka Express'],
    'French': ['Le Petit Bistro', 'Café Paris', 'Chez Laurent', 'Brasserie Lyon', 'La Provence', 'Bistro Bordeaux', 'Le Jardin', 'Maison Blanc', 'Café de Flore', 'L\'Atelier'],
    'Indian': ['Spice Garden', 'Tandoor House', 'Curry Palace', 'Maharaja', 'Saffron Kitchen', 'Bombay Express', 'Delhi Darbar', 'Taj Mahal', 'Monsoon Cafe', 'Garam Masala'],
    'Mexican': ['Taco Fiesta', 'Casa Mexico', 'El Sombrero', 'Aztec Grill', 'Cantina Maya', 'Peppers Mexican', 'Hacienda Real', 'Mariachi Cafe', 'Cinco de Mayo', 'Salsa Verde'],
    'Thai': ['Bangkok Street', 'Thai Orchid', 'Spicy Basil', 'Golden Temple', 'Pad Thai House', 'Lemongrass Cafe', 'Thai Garden', 'Mango Tree', 'Chili Pepper', 'Lotus Blossom'],
    'American': ['The Golden Fork', 'Liberty Grill', 'Stars & Stripes', 'Main Street Diner', 'All American Cafe', 'Eagle\'s Nest', 'Freedom Burger', 'Yankee Kitchen', 'Hometown Grill', 'Patriot\'s Table'],
    'Mediterranean': ['Mediterranean Delight', 'Olive Branch', 'Santorini Blue', 'Cyprus Garden', 'Aegean Sea', 'Greek Islands', 'Mykonos Taverna', 'Athens Corner', 'Poseidon\'s', 'Blue Aegean'],
    'Vietnamese': ['Pho Saigon', 'Mekong Delta', 'Hanoi Kitchen', 'Saigon Pearl', 'Bamboo Pho', 'Vietnam Garden', 'Lotus Cafe', 'Saigon Street', 'Pho King', 'Dragon Bowl']
}

cuisines = list(restaurant_names.keys())
cities = ['New York', 'Los Angeles', 'Chicago', 'San Francisco', 'Miami', 'Seattle', 'Boston', 'Austin', 'Denver', 'Portland', 'Atlanta', 'Dallas', 'Phoenix', 'Philadelphia', 'Houston']

# Function to chunk data for efficient insertion
def chunk_array(array, size):
    chunks = []
    for i in range(0, len(array), size):
        chunks.append(array[i:i + size])
    return chunks

# Generate 5000 restaurant entries
restaurants = []
for i in range(5000):
    cuisine = random.choice(cuisines)
    base_names = restaurant_names[cuisine]
    
    # Create unique restaurant names
    if i < len(base_names) * len(cities):
        name_index = i % len(base_names)
        city_index = (i // len(base_names)) % len(cities)
        name = base_names[name_index]
        city = cities[city_index]
    else:
        name = random.choice(base_names) + f" {random.choice(['Bistro', 'Cafe', 'Restaurant', 'Kitchen', 'Grill'])}"
        city = random.choice(cities)
    
    restaurant = {
        'name': name,
        'cuisine': cuisine,
        'location': f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Park Blvd', 'First St', 'Broadway', 'Market St', 'Union Ave'])}",
        'city': city,
        'capacity': random.randint(25, 250),
        'price_range': random.choice(['$', '$$', '$$$', '$$$$']),
        'rating': round(random.uniform(3.2, 5.0), 1)
    }
    restaurants.append(restaurant)

print(f"Generated {len(restaurants)} restaurant entries")

# Insert data in chunks of 500 (optimal for Supabase)
try:
    # First, clear existing data if needed
    print("Clearing existing restaurant data...")
    supabase.table('restaurants').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    
    # Insert in chunks
    chunks = chunk_array(restaurants, 500)
    total_inserted = 0
    
    for i, chunk in enumerate(chunks):
        print(f"Inserting chunk {i+1}/{len(chunks)} ({len(chunk)} restaurants)...")
        result = supabase.table('restaurants').insert(chunk).execute()
        total_inserted += len(chunk)
        print(f"Successfully inserted {len(chunk)} restaurants. Total: {total_inserted}")
    
    print(f"\n✅ Successfully inserted {total_inserted} restaurants!")
    
    # Verify insertion
    count_result = supabase.table('restaurants').select('id', count='exact').execute()
    print(f"✅ Database now contains {count_result.count} restaurants")
    
    # Show sample data
    sample_result = supabase.table('restaurants').select('name, cuisine, city, rating').limit(10).execute()
    print("\n📋 Sample restaurants added:")
    for restaurant in sample_result.data:
        print(f"- {restaurant['name']} ({restaurant['cuisine']}) - {restaurant['city']} - {restaurant['rating']}⭐")

except Exception as e:
    print(f"❌ Error inserting data: {e}")
