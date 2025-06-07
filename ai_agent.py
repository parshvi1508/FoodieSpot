import os
import json
import logging
import sqlite3
import uuid
import requests
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from together import Together
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RestaurantAI:
    """
    AI Agent for restaurant search, availability checking, and reservation management.
    Uses Together AI for natural language processing with fallback between API and local database.
    """
    
    def __init__(self, api_base_url: Optional[str] = None, db_path: Optional[str] = None, use_api_first: bool = True):
        """
        Initialize the Restaurant AI agent with dual mode support.
        
        Args:
            api_base_url: Base URL for the Flask API
            db_path: Path to SQLite database file for fallback
            use_api_first: Whether to try API first before falling back to database
        """
        # Validate API key
        api_key = os.getenv('TOGETHER_API_KEY')
        if not api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is required")
        
        self.client = Together(api_key=api_key)
        self.context: List[Dict[str, Any]] = []
        self.last_search_results: List[Dict[str, Any]] = []
        
        # API configuration
        self.api_base = api_base_url or os.getenv('API_BASE_URL', 'https://foodiespot-vzs5.onrender.com/api')
        self.use_api_first = use_api_first
        self.api_available = None  # Cache API availability status
        
        # Database configuration for fallback
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'restaurants.db')
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
        """Test both API and database connections on startup."""
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
        
        # Initialize database as fallback
        try:
            self._init_database()
            logger.info("✅ Database fallback ready")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create restaurants table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS restaurants (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        cuisine TEXT,
                        city TEXT,
                        price_range TEXT,
                        rating REAL,
                        phone TEXT,
                        address TEXT,
                        description TEXT,
                        image_url TEXT,
                        capacity INTEGER DEFAULT 50,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create reservations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reservations (
                        id TEXT PRIMARY KEY,
                        restaurant_id TEXT,
                        user_name TEXT NOT NULL,
                        user_email TEXT NOT NULL,
                        party_size INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        special_requests TEXT,
                        status TEXT DEFAULT 'confirmed',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
                    )
                ''')
                
                # Insert sample data if tables are empty
                cursor.execute('SELECT COUNT(*) FROM restaurants')
                if cursor.fetchone()[0] == 0:
                    self._insert_sample_data(cursor)
                
                conn.commit()
                self.db_initialized = True
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _insert_sample_data(self, cursor):
        """Insert sample restaurant data."""
        sample_restaurants = [
            (str(uuid.uuid4()), "Bangkok Street", "Thai", "New York", "$$", 4.5, "555-0101", "123 Thai St", "Authentic Thai cuisine", "", 40),
            (str(uuid.uuid4()), "Amalfi Coast Cafe", "Italian", "New York", "$$$", 4.7, "555-0102", "456 Italian Ave", "Traditional Italian dining", "", 60),
            (str(uuid.uuid4()), "Dragon Palace", "Chinese", "New York", "$$", 4.3, "555-0103", "789 Dragon Rd", "Classic Chinese dishes", "", 80),
            (str(uuid.uuid4()), "Le Petit Bistro", "French", "Paris", "$$$$", 4.8, "555-0104", "321 French Blvd", "Fine French cuisine", "", 35),
            (str(uuid.uuid4()), "Taco Fiesta", "Mexican", "Los Angeles", "$", 4.2, "555-0105", "654 Taco Lane", "Authentic Mexican food", "", 55),
            (str(uuid.uuid4()), "Sakura Sushi", "Japanese", "Los Angeles", "$$$", 4.6, "555-0106", "987 Sushi Way", "Fresh sushi and sashimi", "", 45),
            (str(uuid.uuid4()), "Curry House", "Indian", "Chicago", "$$", 4.4, "555-0107", "246 Spice Ave", "Traditional Indian curry", "", 65),
            (str(uuid.uuid4()), "The Steakhouse", "American", "Chicago", "$$$$", 4.9, "555-0108", "135 Meat St", "Premium steaks and grills", "", 50),
        ]
        
        cursor.executemany('''
            INSERT INTO restaurants (id, name, cuisine, city, price_range, rating, phone, address, description, image_url, capacity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_restaurants)
        
        logger.info("✅ Sample restaurant data inserted")
    
    def _call_api(self, endpoint: str, params: Dict[str, Any], method: str = "POST") -> Optional[Dict[str, Any]]:
        """
        Make API calls with automatic fallback to database.
        
        Args:
            endpoint: API endpoint to call
            params: Parameters to send with the request
            method: HTTP method (GET or POST)
            
        Returns:
            API response data or database fallback result
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
                    logger.warning(f"API Error: {response.status_code}, falling back to database")
                    
            except Exception as e:
                logger.warning(f"API call failed: {e}, falling back to database")
        
        # Fallback to database
        return self._database_fallback(endpoint, params, method)
    
    def _database_fallback(self, endpoint: str, params: Dict[str, Any], method: str) -> Optional[Dict[str, Any]]:
        """Handle database operations as fallback."""
        if not self.db_initialized:
            return None
        
        try:
            if endpoint == "restaurants":
                return self._db_search_restaurants(params)
            elif endpoint == "reservations":
                return self._db_create_reservation(params)
            elif endpoint == "availability":
                return self._db_check_availability(params)
            elif endpoint.startswith("recommendations"):
                return self._db_get_recommendations(params)
            else:
                logger.warning(f"Unknown database endpoint: {endpoint}")
                return None
                
        except Exception as e:
            logger.error(f"Database fallback error: {e}")
            return None
    
    def _db_search_restaurants(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search restaurants in database."""
        query = "SELECT * FROM restaurants WHERE 1=1"
        sql_params = []
        
        if params.get('cuisine'):
            query += " AND LOWER(cuisine) LIKE LOWER(?)"
            sql_params.append(f"%{params['cuisine']}%")
        
        if params.get('city'):
            query += " AND LOWER(city) LIKE LOWER(?)"
            sql_params.append(f"%{params['city']}%")
        
        if params.get('price_range'):
            query += " AND price_range = ?"
            sql_params.append(params['price_range'])
        
        if params.get('min_rating'):
            query += " AND rating >= ?"
            sql_params.append(params['min_rating'])
        
        query += " ORDER BY rating DESC"
        
        restaurants = self._execute_query(query, tuple(sql_params))
        return {
            "success": True,
            "data": restaurants or [],
            "source": "database"
        }
    
    def _db_create_reservation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create reservation in database."""
        reservation_id = str(uuid.uuid4())
        
        result = self._execute_query(
            '''INSERT INTO reservations 
               (id, restaurant_id, user_name, user_email, party_size, date, time, special_requests)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                reservation_id,
                params.get('restaurant_id'),
                params.get('user_name'),
                params.get('user_email'),
                params.get('party_size'),
                params.get('date'),
                params.get('time'),
                params.get('special_requests', '')
            )
        )
        
        if result and result > 0:
            return {
                "success": True,
                "reservation_id": reservation_id,
                "source": "database"
            }
        else:
            return {
                "success": False,
                "error": "Failed to create reservation",
                "source": "database"
            }
    
    def _db_check_availability(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check availability in database."""
        restaurant_name = params.get('restaurant_name', '')
        date = params.get('date', '')
        time = params.get('time', '')
        
        # Get restaurant
        restaurant = self._execute_query(
            "SELECT * FROM restaurants WHERE LOWER(name) = LOWER(?)",
            (restaurant_name,),
            fetch_one=True
        )
        
        if not restaurant:
            return {"success": False, "error": "Restaurant not found", "source": "database"}
        
        # Check existing reservations
        existing = self._execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE restaurant_id = ? AND date = ? AND time = ?",
            (restaurant['id'], date, time)
        )
        
        capacity = restaurant.get('capacity', 50)
        current_reservations = existing[0]['count'] if existing else 0
        available_seats = capacity - current_reservations
        
        return {
            "success": True,
            "available": available_seats > 0,
            "available_seats": available_seats,
            "restaurant_name": restaurant['name'],
            "source": "database"
        }
    
    def _db_get_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations from database."""
        query = "SELECT * FROM restaurants WHERE 1=1"
        sql_params = []
        
        if params.get('cuisine'):
            query += " AND LOWER(cuisine) LIKE LOWER(?)"
            sql_params.append(f"%{params['cuisine']}%")
        
        if params.get('city'):
            query += " AND LOWER(city) LIKE LOWER(?)"
            sql_params.append(f"%{params['city']}%")
        
        if params.get('min_rating'):
            query += " AND rating >= ?"
            sql_params.append(params['min_rating'])
        
        # Map budget to price range
        if params.get('budget'):
            budget_map = {"budget": "$", "moderate": "$$", "upscale": "$$$", "luxury": "$$$$"}
            price_range = budget_map.get(params['budget'])
            if price_range:
                query += " AND price_range = ?"
                sql_params.append(price_range)
        
        query += " ORDER BY rating DESC LIMIT 5"
        
        restaurants = self._execute_query(query, tuple(sql_params))
        
        return {
            "success": True,
            "data": restaurants or [],
            "meta": {
                "message": "Here are my top recommendations based on your preferences",
                "source": "database"
            },
            "source": "database"
        }
    
    def _execute_query(self, query: str, params: tuple = (), fetch_one: bool = False):
        """Execute database query with error handling."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if query.strip().upper().startswith('SELECT'):
                    if fetch_one:
                        result = cursor.fetchone()
                        return dict(result) if result else None
                    else:
                        results = cursor.fetchall()
                        return [dict(row) for row in results]
                else:
                    conn.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return None
    
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
                                "enum": ["$", "$$", "$$$", "$$$$"],
                                "description": "Price range from $ (budget) to $$$$ (luxury)"
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
                                "description": "Name of the restaurant (e.g., 'Bangkok Street', 'Amalfi Coast Cafe')"
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
                                "description": "Name of the restaurant (e.g., 'Bangkok Street', 'Amalfi Coast Cafe')"
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
                                "enum": ["$", "$$", "$$$", "$$$$"],
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
                restaurants_count = self._execute_query("SELECT COUNT(*) as count FROM restaurants")[0]['count']
                reservations_count = self._execute_query("SELECT COUNT(*) as count FROM reservations")[0]['count']
                db_stats = {
                    "restaurants": restaurants_count,
                    "reservations": reservations_count
                }
            
            return {
                "api_available": self.api_available,
                "api_base": self.api_base,
                "database_initialized": self.db_initialized,
                "database_path": self.db_path,
                "database_stats": db_stats,
                "use_api_first": self.use_api_first
            }
        except Exception as e:
            return {"error": str(e)}

# Initialize singleton agent with smart fallback
try:
    ai_agent = RestaurantAI()
    logger.info("Restaurant AI agent initialized successfully")
    status = ai_agent.get_status()
    logger.info(f"System status: API={'✅' if status['api_available'] else '❌'} | DB={'✅' if status['database_initialized'] else '❌'}")
except Exception as e:
    logger.error(f"Failed to initialize Restaurant AI agent: {e}")
    ai_agent = None