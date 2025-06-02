# src/core/recommendations.py
def recommend_restaurants(user_prefs):
    return supabase_client.table('restaurants').select('*').ilike(
        'cuisine', f"%{user_prefs['cuisine']}%"
    ).lte('price_range', user_prefs['max_price']).execute()
