import os
import json
import logging
import requests
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
    Uses Together AI for natural language processing and Flask API for data operations.
    """
    
    def __init__(self, api_base_url: Optional[str] = None):
        """
        Initialize the Restaurant AI agent.
        
        Args:
            api_base_url: Base URL for the Flask API. Defaults to environment variable or production URL.
        """
        # Validate API key
        api_key = os.getenv('TOGETHER_API_KEY')
        if not api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is required")
        
        self.client = Together(api_key=api_key)
        self.context: List[Dict[str, Any]] = []
        self.last_search_results: List[Dict[str, Any]] = []
        
        # FIXED: Use production URL for Render deployment
        self.api_base = api_base_url or os.getenv('API_BASE_URL', 'https://foodiespot-vzs5.onrender.com/api')
        
        # System prompt for better AI behavior
        self.system_prompt = {
            "role": "system",
            "content": """You are a helpful restaurant assistant. You can:
            1. Search for restaurants based on cuisine, location, price range, and ratings
            2. Check availability for specific dates and times
            3. Make reservations for customers
            4. Provide smart recommendations based on user preferences
            You are FoodieSpot AI, a restaurant reservation assistant.
               CRITICAL: When a user wants to make a reservation, you MUST use the create_reservation tool.
                Do NOT just respond conversationally about reservations.

                If a user provides reservation details, immediately call the create_reservation tool with the provided information.

                Required fields for reservations:
                - restaurant_id (get from restaurant name)
                - customer_name
                - customer_email  
                - party_size
                - reservation_date (YYYY-MM-DD format)
                - reservation_time (HH:MM format)
                - special_requests (optional)
                If any required information is missing, ask for it before proceeding.
                Always be polite, helpful, and ask for clarification when needed.
                When making reservations, ensure you have all required information: restaurant, name, email, party size, date, and time."""
        }
        self.context.append(self.system_prompt)
        
        # Define available tools
        self.tools = self._initialize_tools()
    
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
                        "required": ["restaurant_id", "date", "time", "party_size"],
                        "properties": {
                            "restaurant_id": {
                                "type": "string",
                                "description": "Unique identifier for the restaurant"
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
                    "description": "Create a reservation at a restaurant",
                    "parameters": {
                        "type": "object",
                        "required": ["restaurant_id", "customer_name", "customer_email", "party_size", "reservation_date", "reservation_time"],
                        "properties": {
                            "restaurant_id": {
                                "type": "string",
                                "description": "Unique identifier for the restaurant"
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
    
    def _call_api(self, endpoint: str, params: Dict[str, Any], method: str = "POST") -> Optional[Dict[str, Any]]:
        """
        Make API calls to the Flask backend with proper error handling.
        
        Args:
            endpoint: API endpoint to call
            params: Parameters to send with the request
            method: HTTP method (GET or POST)
            
        Returns:
            API response data or None if failed
        """
        try:
            url = f"{self.api_base}/{endpoint}"
            logger.info(f"Making {method} request to: {url}")
            logger.debug(f"Parameters: {params}")
            
            if method == "GET":
                # For GET requests, convert params to query string
                if params:
                    query_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
                    if query_params:
                        url += f"?{query_params}"
                response = requests.get(url, timeout=30)
            else:
                response = requests.post(
                    url, 
                    json=params, 
                    timeout=30,
                    headers={'Content-Type': 'application/json'}
                )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to API")
            return None
        except Exception as e:
            logger.error(f"Unexpected API error: {str(e)}")
            return None
    
    def _process_tool_search_restaurants(self, parameters: Dict[str, Any]) -> str:
        """Process restaurant search tool call."""
        # FIXED: Use the correct endpoint that exists in Flask app
        search_params = {}
        if parameters.get('cuisine'):
            search_params['cuisine'] = parameters['cuisine']
        if parameters.get('location'):
            search_params['city'] = parameters['location']  # Map location to city
        if parameters.get('price_range'):
            search_params['price_range'] = parameters['price_range']
        if parameters.get('min_rating'):
            search_params['min_rating'] = parameters['min_rating']
        
        # Use GET method for restaurant search
        result = self._call_api("restaurants", search_params, method="GET")
        
        if result and result.get('success'):
            restaurants = result['data'][:5]  # Show top 5
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
                
                return f"Found {len(restaurants)} restaurants:\n" + "\n".join(restaurant_info)
        
        return "No restaurants found matching your criteria. Try different search terms or browse our full collection."
    
    def _process_tool_check_availability(self, parameters: Dict[str, Any]) -> str:
        """Process availability check tool call."""
        result = self._call_api("availability", parameters)
        
        if result and result.get('success'):
            restaurant_name = result.get('restaurant_name', 'the restaurant')
            available_seats = result.get('available_seats', 0)
            
            if result.get('available'):
                return f"✅ {restaurant_name} is available! {available_seats} seats remaining for your requested time."
            else:
                return f"❌ {restaurant_name} is not available for your requested time. Only {available_seats} seats remaining."
        
        return "Unable to check availability. Please try again or contact the restaurant directly."
    
    def _process_tool_create_reservation(self, parameters: Dict[str, Any]) -> str:
        logger.info(f"Raw parameters received: {parameters}")
    
    # Get restaurant ID by name if needed
        restaurant_id = parameters.get('restaurant_id')
        if not restaurant_id:
            restaurant_name = parameters.get('restaurant_name')
            if restaurant_name:
                restaurants_result = self._call_api("restaurants", {}, method="GET")
                if restaurants_result and restaurants_result.get('data'):
                    restaurant = next((r for r in restaurants_result['data'] 
                                    if r['name'].lower() == restaurant_name.lower()), None)
                    if restaurant:
                        restaurant_id = restaurant['id']
    
    # FIXED: Proper data formatting with validation
        try:
            reservation_data = {
            "restaurant_id": str(restaurant_id) if restaurant_id else "",
            "user_name": str(parameters.get('customer_name', '')),
            "user_email": str(parameters.get('customer_email', '')),
            "party_size": int(parameters.get('party_size', 0)),
            "date": str(parameters.get('reservation_date', '')),
            "time": str(parameters.get('reservation_time', '')),
            "special_requests": str(parameters.get('special_requests', ''))
        }
        
        # Validate required fields are not empty
            required_fields = ['restaurant_id', 'user_name', 'user_email', 'party_size', 'date', 'time']
            missing_fields = [field for field in required_fields 
                            if not reservation_data.get(field) or reservation_data[field] == "" or reservation_data[field] == 0]
        
            if missing_fields:
                error_msg = f"Missing required information: {', '.join(missing_fields)}"
                logger.error(error_msg)
                return error_msg
        
            logger.info(f"Formatted reservation data: {reservation_data}")
        
        # Make API call
            result = self._call_api("reservations", reservation_data, method="POST")
            logger.info(f"API call result: {result}")
        
            if result and result.get('success'):
                return "🎉 Reservation confirmed! Your table has been booked successfully."
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'API connection failed'
                logger.error(f"Reservation creation failed: {error_msg}")
                return f"❌ Reservation failed: {error_msg}"
            
        except Exception as e:
            logger.error(f"Exception during reservation creation: {str(e)}")
            return f"❌ Error creating reservation: {str(e)}"

    def _process_tool_get_recommendations(self, parameters: Dict[str, Any]) -> str:
        """Process smart recommendations tool call."""
        logger.info(f"Getting recommendations with parameters: {parameters}")
        
        result = self._call_api("recommendations/smart", parameters, method="POST")
        logger.info(f"API result: {result}")
        
        if result and result.get('success'):
            recommendations = result['data'][:5]
            meta = result.get('meta', {})
            
            if recommendations:
                restaurant_info = []
                for restaurant in recommendations:
                    name = restaurant.get('name', 'Unknown')
                    cuisine = restaurant.get('cuisine', 'N/A')
                    rating = restaurant.get('rating', 'N/A')
                    price = restaurant.get('price_range', 'N/A')
                    restaurant_info.append(f"• {name} ({cuisine}, {rating}⭐, {price})")
                
                message = meta.get('message', 'Found great recommendations')
                return f"{message}\n\n" + "\n".join(restaurant_info)
        
        logger.warning("No recommendations found or API call failed")
        return "I couldn't generate recommendations right now. Please try browsing our restaurant collection."
    
    def _process_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Execute tool calls with proper error handling and logging.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            
        Returns:
            Result of the tool execution
        """
        logger.info(f"Processing tool: {tool_name}")
        logger.debug(f"Parameters: {parameters}")
        
        try:
            if tool_name == "search_restaurants":
                return self._process_tool_search_restaurants(parameters)
            
            elif tool_name == "check_availability":
                return self._process_tool_check_availability(parameters)
            
            elif tool_name == "create_reservation":
                return self._process_tool_create_reservation(parameters)
            
            elif tool_name == "get_recommendations":  # FIXED: Added this line
                return self._process_tool_get_recommendations(parameters)
            
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            logger.error(f"Error processing tool {tool_name}: {str(e)}")
            return f"Error executing {tool_name}. Please try again."
    
    def chat(self, user_input: str) -> str:
        """
        Process user input and generate AI response with tool calls.
        
        Args:
            user_input: User's message
            
        Returns:
            AI agent's response
        """
        if not user_input.strip():
            return "Please provide a message. How can I help you with restaurants today?"
        
        # Add user message to context
        user_message = {"role": "user", "content": user_input.strip()}
        self.context.append(user_message)
        
        # Keep context manageable (last 15 messages to stay within free tier limits)
        if len(self.context) > 15:
            self.context = [self.system_prompt] + self.context[-14:]
        
        try:
            # Get AI response
            response = self.client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                messages=self.context,
                tools=self.tools,
                temperature=0.7,
                max_tokens=800  # Reduced for free tier efficiency
            )
            
            msg = response.choices[0].message
            
            # Add assistant message to context
            assistant_message = {
                "role": "assistant", 
                "content": msg.content or "",
                "tool_calls": getattr(msg, 'tool_calls', None)
            }
            self.context.append(assistant_message)
            
            # Process tool calls if any
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_results = []
                
                for tool_call in msg.tool_calls:
                    try:
                        # Parse tool parameters
                        parameters = json.loads(tool_call.function.arguments)
                        
                        # Execute tool
                        result = self._process_tool(tool_call.function.name, parameters)
                        tool_results.append(result)
                        
                        # Add tool result to context
                        tool_message = {
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call.id
                        }
                        self.context.append(tool_message)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error for tool call: {e}")
                        error_result = "Error parsing tool parameters"
                        tool_results.append(error_result)
                        
                        tool_message = {
                            "role": "tool",
                            "content": error_result,
                            "tool_call_id": tool_call.id
                        }
                        self.context.append(tool_message)
                
                # Get final response with tool results
                try:
                    final_response = self.client.chat.completions.create(
                        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                        messages=self.context,
                        temperature=0.7,
                        max_tokens=600
                    )
                    
                    final_msg = final_response.choices[0].message
                    final_content = final_msg.content or "I've processed your request."
                    
                    # Add final response to context
                    final_assistant_message = {
                        "role": "assistant",
                        "content": final_content
                    }
                    self.context.append(final_assistant_message)
                    
                    return final_content
                    
                except Exception as e:
                    logger.error(f"Error getting final response: {e}")
                    return "I've completed your request, but had trouble generating a final response."
            
            return msg.content or "I'm here to help with restaurants. What would you like to know?"
            
        except Exception as e:
            logger.error(f"Chat processing error: {str(e)}")
            error_msg = "I'm having trouble processing your request right now. Please try again in a moment."
            
            # Add error message to context
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

# Initialize singleton agent
try:
    ai_agent = RestaurantAI()
    logger.info("Restaurant AI agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Restaurant AI agent: {e}")
    ai_agent = None
