# Supabase operations
# src/core/database.py
from supabase import create_client
import os

class SupabaseClient:
    def __init__(self):
        self.client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    
    def get_restaurants(self):
        return self.client.table('restaurants').select('*').execute()
