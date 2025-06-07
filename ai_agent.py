import os
import json
import logging
import uuid
import requests
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from together import Together
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RestaurantAI:
    """
    AI Agent for restaurant search, availability checking, and reservation management.
    Uses Together AI for natural language processing with fallback between API and Supabase database.
    """
    
    def __init__(self, api_base_url: Optional[str] = None, use_api_first: bool = True):
        """
        Initialize the Restaurant AI agent with dual mode support.
        
        Args:
            api_base_url: Base URL for the Flask API
            use_api_first: Whether to try API first before falling back to database
        """
        # Validate API key
        api_key = os.getenv('TOGETHER_API_KEY')
        if not api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is required")
        
        # Validate Supabase credentials
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")
        
        self.client = Together(api_key=api_key)
        self.context: List[Dict[str, Any]] = []
        self.last_search_results: List[Dict[str, Any]] = []
        
        # API configuration
        self.api_base = api_base_url or os.getenv('API_BASE_URL', 'https://foodiespot-vzs5.onrender.com/api')
        self.use_api_first = use_api_first
        self.api_available = None  # Cache API availability status
        
        # Supabase configuration for fallback
        self.supabase: Client = create_client(supabase_url, supabase_anon_key)
        self.db_initialized = False
        
        # Test connections on startup
        self._test_connections()
        
        # System prompt for better AI behavior
        self.system_prompt = {
            "role": "system",
            "content": """You are FoodieSpot AI, a restaurant reservation assistant. You can:
            1. Search for restaurants based on cuisine, location, price range, and ratings
            2. Check availability for specific dates and times
            3. Make reservations for customers
            4. Provide smart recommendations based on user preferences
            
            CRITICAL: When a user wants to make a reservation, you MUST use the create_reservation tool.
            Do NOT just respond conversationally about reservations.

            If a user provides reservation details, immediately call the create_reservation tool with the provided information.

            Required fields for reservations:
            - restaurant_name (name of the restaurant)
            - customer_name
            - customer_email  
            - party_size
            - reservation_date (YYYY-MM-DD format)
            - reservation_time (HH:MM format)
            - special_requests (optional)
            
            If any required information is missing, ask for it before proceeding.
            Always be polite, helpful, and ask for clarification when needed."""
        }
        self.context.append(self.system_prompt)
        
        # Define available tools
        self.tools = self._initialize_tools()
    
    def _test_connections(self):
        """Test both API and Supabase connections on startup."""
        # Test API connection
        try:
            response = requests.get(f"{self.api_base}/restaurants", timeout=5)
            if response.status_code == 200:
                self.api_available = True
                logger.info("✅ API connection successful")
            else:
                self.api_available = False
                logger.warning(f"⚠️ API returned status {response.status_code}")
        except Exception as e:
            self.api_available = False
            logger.warning(f"⚠️ API connection failed: {e}")
        
        # Test Supabase connection and initialize
        try:
            self._init_supabase()
            logger.info("✅ Supabase connection successful")
        except Exception as e:
            logger.error(f"❌ Supabase initialization failed: {e}")
    
    def _init_supabase(self):
        """Initialize Supabase tables and sample data if needed."""
        try:
            # Check if restaurants table exists and has data
            result = self.supabase.table('restaurants').select('id').limit(1).execute()
            
            if len(result.data) == 0:
                logger.info("No restaurants found, inserting sample data...")
                self._insert_sample_data_supabase()
            
            self.db_initialized = True
            logger.info("✅ Supabase database ready")
            
        except Exception as e:
            logger.error(f"❌ Supabase initialization failed: {e}")
            # Try to create tables if they don't exist (this would need to be done via Supabase dashboard or SQL)
            logger.info("Please ensure the following tables exist in your Supabase database:")
            logger.info("""
            -- Restaurants table
            CREATE TABLE restaurants (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                cuisine TEXT,
                city TEXT,
                price_range TEXT,
                rating DECIMAL(2,1),
                phone TEXT,
                address TEXT,
                description TEXT,
                image_url TEXT,
                capacity INTEGER DEFAULT 50,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Reservations table
            CREATE TABLE reservations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                restaurant_id UUID REFERENCES restaurants(id),
                user_name TEXT NOT NULL,
                user_email TEXT NOT NULL,
                party_size INTEGER NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                special_requests TEXT,
                status TEXT DEFAULT 'confirmed',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """)
            raise
    
    def _insert_sample_data_supabase(self):
        """Insert sample restaurant data into Supabase."""
        sample_restaurants = [
            {
                "name": "Bangkok Street",
                "cuisine": "Thai",
                "city": "New York",
                "price_range": "$$",
                "rating": 4.5,
                "phone": "555-0101",
                "address": "123 Thai St",
                "description": "Authentic Thai cuisine",
                "image_url": "",
                "capacity": 40
            },
            {
                "name": "Amalfi Coast Cafe",
                "cuisine": "Italian",
                "city": "New York",
                "price_range": "$$$",
                "rating": 4.7,
                "phone": "555-0102",
                "address": "456 Italian Ave",
                "description": "Traditional Italian dining",
                "image_url": "",
                "capacity": 60
            },
            {
                "name": "Dragon Palace",
                "cuisine": "Chinese",
                "city": "New York",
                "price_range": "$$",
                "rating": 4.3,
                "phone": "555-0103",
                "address": "789 Dragon Rd",
                "description": "Classic Chinese dishes",
                "image_url": "",
                "capacity": 80
            },
            {
                "name": "Le Petit Bistro",
                "cuisine": "French",
                "city": "Paris",
                "price_range": "$$$$",
                "rating": 4.8,
                "phone": "555-0104",
                "address": "321 French Blvd",
                "description": "Fine French cuisine",
                "image_url": "",
                "capacity": 35
            },
            {
                "name": "Taco Fiesta",
                "cuisine": "Mexican",
                "city": "Los Angeles",
                "price_range": "$",
                "rating": 4.2,
                "phone": "555-0105",
                "address": "654 Taco Lane",
                "description": "Authentic Mexican food",
                "image_url": "",
                "capacity": 55
            },
            {
                "name": "Sakura Sushi",
                "cuisine": "Japanese",
                "city": "Los Angeles",
                "price_range": "$$$",
                "rating": 4.6,
                "phone": "555-0106",
                "address": "987 Sushi Way",
                "description": "Fresh sushi and sashimi",
                "image_url": "",
                "capacity": 45
            },
            {
                "name": "Curry House",
                "cuisine": "Indian",
                "city": "Chicago",
                "price_range": "$$",
                "rating": 4.4,
                "phone": "555-0107",
                "address": "246 Spice Ave",
                "description": "Traditional Indian curry",
                "image_url": "",
                "capacity": 65
            },
            {
                "name": "The Steakhouse",
                "cuisine": "American",
                "city": "Chicago",
                "price_range": "$$$$",
                "rating": 4.9,
                "phone": "555-0108",
                "address": "135 Meat St",
                "description": "Premium steaks and grills",
                "image_url": "",
                "capacity": 50
            }
        ]
        
        try:
            result = self.supabase.table('restaurants').insert(sample_restaurants).execute()
            logger.info(f"✅ Inserted {len(sample_restaurants)} sample restaurants")
        except Exception as e:
            logger.error(f"❌ Failed to insert sample data: {e}")
    
    def _call_api(self, endpoint: str, params: Dict[str, Any], method: str = "POST") -> Optional[Dict[str, Any]]:
        """
        Make API calls with automatic fallback to Supabase.
        
        Args:
            endpoint: API endpoint to call
            params: Parameters to send with the request
            method: HTTP method (GET or POST)
            
        Returns:
            API response data or Supabase fallback result
        """
        # Try API first if available and preferred
        if self.use_api_first and self.api_available:
            try:
                url = f"{self.api_base}/{endpoint}"
                logger.info(f"Making {method} request to: {url}")
                
                if method == "GET":
                    if params:
                        query_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
                        if query_params:
                            url += f"?{query_params}"
                    response = requests.get(url, timeout=10)
                else:
                    response = requests.post(
                        url, 
                        json=params, 
                        timeout=10,
                        headers={'Content-Type': 'application/json'}
                    )
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.warning(f"API Error: {response.status_code}, falling back to Supabase")
                    
            except Exception as e:
                logger.warning(f"API call failed: {e}, falling back to Supabase")
        
        # Fallback to Supabase
        return self._supabase_fallback(endpoint, params, method)
    
    def _supabase_fallback(self, endpoint: str, params: Dict[str, Any], method: str) -> Optional[Dict[str, Any]]:
        """Handle Supabase operations as fallback."""
        if not self.db_initialized:
            return None
        
        try:
            if endpoint == "restaurants":
                return self._supabase_search_restaurants(params)
            elif endpoint == "reservations":
                return self._supabase_create_reservation(params)
            elif endpoint == "availability":
                return self._supabase_check_availability(params)
            elif endpoint.startswith("recommendations"):
                return self._supabase_get_recommendations(params)
            else:
                logger.warning(f"Unknown Supabase endpoint: {endpoint}")
                return None
                
        except Exception as e:
            logger.error(f"Supabase fallback error: {e}")
            return None
    
    def _supabase_search_restaurants(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search restaurants in Supabase."""
        try:
            query = self.supabase.table('restaurants').select('*')
            
            if params.get('cuisine'):
                query = query.ilike('cuisine', f"%{params['cuisine']}%")
            
            if params.get('city'):
                query = query.ilike('city', f"%{params['city']}%")
            
            if params.get('price_range'):
                query = query.eq('price_range', params['price_range'])
            
            if params.get('min_rating'):
                query = query.gte('rating', params['min_rating'])
            
            query = query.order('rating', desc=True)
            result = query.execute()
            
            return {
                "success": True,
                "data": result.data or [],
                "source": "supabase"
            }
            
        except Exception as e:
            logger.error(f"Supabase search error: {e}")
            return {"success": False, "error": str(e), "source": "supabase"}
    
    def _supabase_create_reservation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create reservation in Supabase."""
        try:
            reservation_data = {
                "restaurant_id": params.get('restaurant_id'),
                "user_name": params.get('user_name'),
                "user_email": params.get('user_email'),
                "party_size": params.get('party_size'),
                "date": params.get('date'),
                "time": params.get('time'),
                "special_requests": params.get('special_requests', '')
            }
            
            result = self.supabase.table('reservations').insert(reservation_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "reservation_id": result.data[0]['id'],
                    "source": "supabase"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create reservation",
                    "source": "supabase"
                }
                
        except Exception as e:
            logger.error(f"Supabase reservation error: {e}")
            return {"success": False, "error": str(e), "source": "supabase"}
    
    def _supabase_check_availability(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check availability in Supabase."""
        try:
            restaurant_name = params.get('restaurant_name', '')
            date = params.get('date', '')
            time = params.get('time', '')
            
            # Get restaurant
            restaurant_result = self.supabase.table('restaurants').select('*').ilike('name', restaurant_name).limit(1).execute()
            
            if not restaurant_result.data:
                return {"success": False, "error": "Restaurant not found", "source": "supabase"}
            
            restaurant = restaurant_result.data[0]
            
            # Check existing reservations for the same date and time
            reservations_result = self.supabase.table('reservations').select('party_size').eq('restaurant_id', restaurant['id']).eq('date', date).eq('time', time).execute()
            
            capacity = restaurant.get('capacity', 50)
            current_bookings = sum(r['party_size'] for r in reservations_result.data)
            available_seats = capacity - current_bookings
            
            return {
                "success": True,
                "available": available_seats > 0,
                "available_seats": max(0, available_seats),
                "restaurant_name": restaurant['name'],
                "source": "supabase"
            }
            
        except Exception as e:
            logger.error(f"Supabase availability error: {e}")
            return {"success": False, "error": str(e), "source": "supabase"}
    
    def _supabase_get_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations from Supabase."""
        try:
            query = self.supabase.table('restaurants').select('*')
            
            if params.get('cuisine'):
                query = query.ilike('cuisine', f"%{params['cuisine']}%")
            
            if params.get('city'):
                query = query.ilike('city', f"%{params['city']}%")
            
            if params.get('min_rating'):
                query = query.gte('rating', params['min_rating'])
            
            # Map budget to price range
            if params.get('budget'):
                budget_map = {"budget": "$", "moderate": "$", "upscale": "$$", "luxury": "$$"}
                price_range = budget_map.get(params['budget'])
                if price_range:
                    query = query.eq('price_range', price_range)
            
            if params.get('price_range'):
                query = query.eq('price_range', params['price_range'])
            
            query = query.order('rating', desc=True).limit(5)
            result = query.execute()
            
            return {
                "success": True,
                "data": result.data or [],
                "meta": {
                    "message": "Here are my top recommendations based on your preferences",
                    "source": "supabase"
                },
                "source": "supabase"
            }
            
        except Exception as e:
            logger.error(f"Supabase recommendations error: {e}")
            return {"success": False, "error": str(e), "source": "supabase"}
    
    def _validate_and_fix_date(self, date_str: str) -> str:
        """Validate and fix date format, handling 2024/2025 issue."""
        try:
            # Parse the input date
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Get current date
            current_date = date.today()
            
            # If the parsed date is in the past (e.g., 2024), update to current year
            if parsed_date < current_date:
                # Check if it's a year issue
                if parsed_date.year < current_date.year:
                    # Update to current year
                    fixed_date = parsed_date.replace(year=current_date.year)
                    logger.info(f"Date corrected from {date_str} to {fixed_date.isoformat()}")
                    return fixed_date.isoformat()
                else:
                    # Date is in the past but same year - could be valid for same-day reservations
                    if (current_date - parsed_date).days > 1:
                        logger.warning(f"Date {date_str} is more than 1 day in the past")
            
            return date_str
            
        except ValueError as e:
            logger.error(f"Invalid date format: {date_str}, error: {e}")
            # Return current date as fallback
            return date.today().isoformat()
    
    def _initialize_tools(self) -> List[Dict[str, Any]]:
        """Initialize the available tools for the AI agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_restaurants",
                    "description": "Search for restaurants based on various criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cuisine": {
                                "type": "string",
                                "description": "Type of cuisine (e.g., Italian, Chinese, Mexican)"
                            },
                            "location": {
                                "type": "string",
                                "description": "Location or area to search in"
                            },
                            "price_range": {
                                "type": "string",
                                "enum": ["$", "$", "$$", "$$"],
                                "description": "Price range from $ (budget) to $$ (luxury)"
                            },
                            "min_rating": {
                                "type": "number",
                                "minimum": 1,
                                "maximum": 5,
                                "description": "Minimum rating (1-5 stars)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": "Check if a restaurant has availability for a specific date and time",
                    "parameters": {
                        "type": "object",
                        "required": ["restaurant_name", "date", "time", "party_size"],
                        "properties": {
                            "restaurant_name": {
                                "type": "string",
                                "description": "Name of the restaurant"
                            },
                            "date": {
                                "type": "string",
                                "description": "Reservation date in YYYY-MM-DD format"
                            },
                            "time": {
                                "type": "string",
                                "description": "Reservation time in HH:MM format (24-hour)"
                            },
                            "party_size": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Number of people in the party"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_reservation",
                    "description": "Create a new restaurant reservation",
                    "parameters": {
                        "type": "object",
                        "required": ["restaurant_name", "customer_name", "customer_email", "party_size", "reservation_date", "reservation_time"],
                        "properties": {
                            "restaurant_name": {
                                "type": "string",
                                "description": "Name of the restaurant"
                            },
                            "customer_name": {
                                "type": "string",
                                "description": "Full name of the customer making the reservation"
                            },
                            "customer_email": {
                                "type": "string",
                                "format": "email",
                                "description": "Email address of the customer"
                            },
                            "party_size": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Number of people in the party"
                            },
                            "reservation_date": {
                                "type": "string",
                                "description": "Reservation date in YYYY-MM-DD format"
                            },
                            "reservation_time": {
                                "type": "string",
                                "description": "Reservation time in HH:MM format (24-hour)"
                            },
                            "special_requests": {
                                "type": "string",
                                "description": "Any special requests or dietary requirements"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recommendations",
                    "description": "Get smart restaurant recommendations based on user preferences",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cuisine": {
                                "type": "string",
                                "description": "Preferred cuisine type"
                            },
                            "city": {
                                "type": "string", 
                                "description": "Preferred location/city"
                            },
                            "budget": {
                                "type": "string",
                                "enum": ["budget", "moderate", "upscale", "luxury"],
                                "description": "Budget preference"
                            },
                            "price_range": {
                                "type": "string",
                                "enum": ["$", "$", "$$", "$$"],
                                "description": "Price range preference"
                            },
                            "min_rating": {
                                "type": "number",
                                "minimum": 1,
                                "maximum": 5,
                                "description": "Minimum rating requirement"
                            },
                            "party_size": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Number of people"
                            }
                        }
                    }
                }
            }
        ]
    
    def _process_tool_search_restaurants(self, parameters: Dict[str, Any]) -> str:
        """Process restaurant search tool call."""
        search_params = {}
        if parameters.get('cuisine'):
            search_params['cuisine'] = parameters['cuisine']
        if parameters.get('location'):
            search_params['city'] = parameters['location']
        if parameters.get('price_range'):
            search_params['price_range'] = parameters['price_range']
        if parameters.get('min_rating'):
            search_params['min_rating'] = parameters['min_rating']
        
        result = self._call_api("restaurants", search_params, method="GET")
        
        if result and result.get('success'):
            restaurants = result['data'][:5]
            if restaurants:
                self.last_search_results = restaurants
                restaurant_info = []
                
                for restaurant in restaurants:
                    name = restaurant.get('name', 'Unknown')
                    cuisine = restaurant.get('cuisine', 'N/A')
                    rating = restaurant.get('rating', 'N/A')
                    price = restaurant.get('price_range', 'N/A')
                    city = restaurant.get('city', 'N/A')
                    restaurant_info.append(f"• {name} ({cuisine}, {rating}⭐, {price}) - {city}")
                
                source = result.get('source', 'api')
                return f"Found {len(restaurants)} restaurants (via {source}):\n" + "\n".join(restaurant_info)
        
        return "No restaurants found matching your criteria. Try different search terms."
    
    def _process_tool_check_availability(self, parameters: Dict[str, Any]) -> str:
        """Process availability check tool call."""
        # Validate and fix date if needed
        if parameters.get('date'):
            parameters['date'] = self._validate_and_fix_date(parameters['date'])
        
        result = self._call_api("availability", parameters)
        
        if result and result.get('success'):
            restaurant_name = parameters.get('restaurant_name', 'the restaurant')
            available_seats = result.get('available_seats', 0)
            source = result.get('source', 'api')
            
            if result.get('available'):
                return f"✅ {restaurant_name} is available! {available_seats} seats remaining for your requested time. (via {source})"
            else:
                return f"❌ {restaurant_name} is not available for your requested time. Only {available_seats} seats remaining. (via {source})"
        
        return "Unable to check availability. Please try again or contact the restaurant directly."
    
    def _process_tool_create_reservation(self, parameters: Dict[str, Any]) -> str:
        """Handle reservation creation with restaurant name lookup and date validation."""
        logger.info(f"Creating reservation with parameters: {parameters}")
        
        restaurant_name = parameters.get('restaurant_name', '')
        
        # Validate and fix date if needed
        if parameters.get('reservation_date'):
            original_date = parameters['reservation_date']
            fixed_date = self._validate_and_fix_date(original_date)
            if original_date != fixed_date:
                logger.info(f"Reservation date corrected from {original_date} to {fixed_date}")
                parameters['reservation_date'] = fixed_date
        
        # Look up restaurant ID
        restaurants_result = self._call_api("restaurants", {}, method="GET")
        if not restaurants_result or not restaurants_result.get('data'):
            return "❌ Could not access restaurant database. Please try again."
        
        restaurant = next((r for r in restaurants_result['data'] 
                         if r['name'].lower() == restaurant_name.lower()), None)
        
        if not restaurant:
            available_restaurants = [r['name'] for r in restaurants_result['data'][:5]]
            return f"❌ Restaurant '{restaurant_name}' not found. Available restaurants: {', '.join(available_restaurants)}"
        
        # Validate required fields
        required_fields = ['customer_name', 'customer_email', 'party_size', 'reservation_date', 'reservation_time']
        for field in required_fields:
            if not parameters.get(field):
                return f"❌ Missing required field: {field}"
        
        try:
            reservation_data = {
                "restaurant_id": restaurant['id'],
                "user_name": str(parameters['customer_name']),
                "user_email": str(parameters['customer_email']),
                "party_size": int(parameters['party_size']),
                "date": str(parameters['reservation_date']),
                "time": str(parameters['reservation_time']),
                "special_requests": str(parameters.get('special_requests', ''))
            }
            
            result = self._call_api("reservations", reservation_data, method="POST")
            
            if result and result.get('success'):
                source = result.get('source', 'api')
                reservation_id = result.get('reservation_id', 'N/A')
                return f"🎉 Reservation confirmed at {restaurant_name}! Reservation ID: {reservation_id} (via {source})\n\nDetails:\n• Date: {parameters['reservation_date']}\n• Time: {parameters['reservation_time']}\n• Party Size: {parameters['party_size']}\n• Customer: {parameters['customer_name']}"
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Service unavailable'
                return f"❌ Reservation failed: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            return f"❌ Error creating reservation: {str(e)}"
    
    def _process_tool_get_recommendations(self, parameters: Dict[str, Any]) -> str:
        """Process smart recommendations tool call."""
        result = self._call_api("recommendations/smart", parameters, method="POST")
        
        if result and result.get('success'):
            recommendations = result['data'][:5]
            meta = result.get('meta', {})
            source = result.get('source', 'api')
            
            if recommendations:
                restaurant_info = []
                for restaurant in recommendations:
                    name = restaurant.get('name', 'Unknown')
                    cuisine = restaurant.get('cuisine', 'N/A')
                    rating = restaurant.get('rating', 'N/A')
                    price = restaurant.get('price_range', 'N/A')
                    city = restaurant.get('city', 'N/A')
                    restaurant_info.append(f"• {name} ({cuisine}, {rating}⭐, {price}) - {city}")
                
                message = meta.get('message', 'Found great recommendations')
                return f"{message} (via {source}):\n\n" + "\n".join(restaurant_info)
        
        return "I couldn't generate recommendations right now. Please try browsing our restaurant collection."
    
    def _process_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute tool calls with proper error handling and logging."""
        logger.info(f"Processing tool: {tool_name}")
        
        try:
            if tool_name == "search_restaurants":
                return self._process_tool_search_restaurants(parameters)
            elif tool_name == "check_availability":
                return self._process_tool_check_availability(parameters)
            elif tool_name == "create_reservation":
                return self._process_tool_create_reservation(parameters)
            elif tool_name == "get_recommendations":
                return self._process_tool_get_recommendations(parameters)
            else:
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            logger.error(f"Error processing tool {tool_name}: {str(e)}")
            return f"Error executing {tool_name}. Please try again."
    
    def chat(self, user_input: str) -> str:
        """Process user input and generate AI response with tool calls."""
        if not user_input.strip():
            return "Please provide a message. How can I help you with restaurants today?"
        
        user_message = {"role": "user", "content": user_input.strip()}
        self.context.append(user_message)
        
        # Keep context manageable
        if len(self.context) > 15:
            self.context = [self.system_prompt] + self.context[-14:]
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                messages=self.context,
                tools=self.tools,
                temperature=0.7,
                max_tokens=800
            )
            
            msg = response.choices[0].message
            
            assistant_message = {
                "role": "assistant", 
                "content": msg.content or "",
                "tool_calls": getattr(msg, 'tool_calls', None)
            }
            self.context.append(assistant_message)
            
            # Process tool calls if any
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    try:
                        parameters = json.loads(tool_call.function.arguments)
                        result = self._process_tool(tool_call.function.name, parameters)
                        
                        tool_message = {
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call.id
                        }
                        self.context.append(tool_message)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error: {e}")
                        error_result = "Error parsing tool parameters"
                        tool_message = {
                            "role": "tool",
                            "content": error_result,
                            "tool_call_id": tool_call.id
                        }
                        self.context.append(tool_message)
                
                # Get final response
                try:
                    final_response = self.client.chat.completions.create(
                        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                        messages=self.context,
                        temperature=0.7,
                        max_tokens=600
                    )
                    
                    final_content = final_response.choices[0].message.content or "I've processed your request."
                    
                    self.context.append({
                        "role": "assistant",
                        "content": final_content
                    })
                    
                    return final_content
                    
                except Exception as e:
                    logger.error(f"Error getting final response: {e}")
                    return "I've completed your request, but had trouble generating a final response."
            
            return msg.content or "I'm here to help with restaurants. What would you like to know?"
            
        except Exception as e:
            logger.error(f"Chat processing error: {str(e)}")
            error_msg = "I'm having trouble processing your request right now. Please try again in a moment."
            self.context.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    def reset_conversation(self):
        """Reset the conversation context."""
        self.context = [self.system_prompt]
        self.last_search_results = []
        logger.info("Conversation context reset")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history."""
        return [msg for msg in self.context if msg["role"] != "system"]
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status for debugging."""
        try:
            db_stats = {}
            if self.db_initialized:
                restaurants_result = self.supabase.table('restaurants').select('id', count='exact').execute()
                reservations_result = self.supabase.table('reservations').select('id', count='exact').execute()
                db_stats = {
                    "restaurants": restaurants_result.count,
                    "reservations": reservations_result.count
                }
            
            return {
                "api_available": self.api_available,
                "api_base": self.api_base,
                "database_initialized": self.db_initialized,
                "database_type": "supabase",
                "database_stats": db_stats,
                "use_api_first": self.use_api_first
            }
        except Exception as e:
            return {"error": str(e)}

# Initialize singleton agent with Supabase fallback
try:
    ai_agent = RestaurantAI()
    logger.info("Restaurant AI agent initialized successfully with Supabase")
    status = ai_agent.get_status()
    logger.info(f"System status: API={'✅' if status['api_available'] else '❌'} | Supabase={'✅' if status['database_initialized'] else '❌'}")
    if status.get('database_stats'):
        logger.info(f"Database contains {status['database_stats']['restaurants']} restaurants and {status['database_stats']['reservations']} reservations")
except Exception as e:
    logger.error(f"Failed to initialize Restaurant AI agent: {e}")
    ai_agent = None