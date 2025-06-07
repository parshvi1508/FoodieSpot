import streamlit as st
import requests
import json
from datetime import datetime, date, timedelta
import pandas as pd
import logging
from ai_agent import ai_agent
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="FoodieSpot AI - Premium Dining Experience",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load environment variables
load_dotenv()
API_BASE_URL = os.getenv('API_BASE_URL', 'https://foodiespot-vzs5.onrender.com/api')

# Enhanced Responsive CSS with Professional Food Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;500;600;700;800&family=Roboto:wght@300;400;500;600;700&display=swap');
    
    /* Global Reset with Enhanced Food Colors */
    .stApp {
        background: linear-gradient(135deg, 
            rgba(215, 53, 39, 0.08) 0%,
            rgba(244, 162, 97, 0.06) 20%,
            rgba(139, 90, 60, 0.08) 40%,
            rgba(205, 133, 63, 0.06) 60%,
            rgba(160, 82, 45, 0.08) 80%,
            rgba(218, 165, 32, 0.06) 100%
        );
        background-attachment: fixed;
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        color: #2c1810;
    }
    
    /* Enhanced Navigation Header */
    .nav-header {
        background: rgba(255, 255, 255, 0.35);
        backdrop-filter: blur(30px);
        border: 2px solid rgba(215, 53, 39, 0.25);
        border-radius: 25px;
        padding: 2rem 2.5rem;
        margin-bottom: 2.5rem;
        box-shadow: 0 20px 60px rgba(215, 53, 39, 0.12);
        position: sticky;
        top: 0.5rem;
        z-index: 100;
    }
    
    .nav-title {
        font-family: 'Playfair Display', serif;
        font-size: clamp(2.5rem, 5vw, 4.5rem);
        font-weight: 800;
        background: linear-gradient(135deg, #d73527 0%, #e76f51 25%, #f4a261 50%, #e9c46a 75%, #daa520 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 0;
        letter-spacing: -1px;
    }
    
    .nav-subtitle {
        text-align: center;
        color: rgba(139, 90, 60, 0.9);
        font-size: clamp(1rem, 2.5vw, 1.4rem);
        margin-top: 0.8rem;
        font-weight: 500;
        font-family: 'Roboto', sans-serif;
        letter-spacing: 0.5px;
    }
    
    /* Enhanced Glass Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.35);
        backdrop-filter: blur(25px);
        border: 2px solid rgba(215, 53, 39, 0.2);
        border-radius: 20px;
        padding: clamp(1.5rem, 4vw, 3rem);
        margin: clamp(1rem, 3vw, 2.5rem) 0;
        box-shadow: 0 15px 50px rgba(215, 53, 39, 0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .glass-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 25px 70px rgba(215, 53, 39, 0.15);
        border-color: rgba(215, 53, 39, 0.4);
    }
    
    /* Enhanced Restaurant Cards */
    .restaurant-card {
        background: rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(20px);
        border: 2px solid rgba(215, 53, 39, 0.25);
        border-radius: 18px;
        padding: clamp(1.2rem, 3vw, 2.5rem);
        margin: clamp(1rem, 2vw, 2rem) 0;
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
    }
    
    .restaurant-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 20px 60px rgba(215, 53, 39, 0.2);
        background: rgba(255, 255, 255, 0.4);
        border-color: rgba(215, 53, 39, 0.4);
    }
    
    .restaurant-name {
        font-family: 'Playfair Display', serif;
        font-size: clamp(1.4rem, 3vw, 2.2rem);
        font-weight: 700;
        color: #8b5a3c;
        margin-bottom: 0.8rem;
        letter-spacing: -0.5px;
    }
    
    .restaurant-details {
        color: rgba(139, 90, 60, 0.9);
        line-height: 1.7;
        font-size: clamp(0.9rem, 2vw, 1.1rem);
        font-family: 'Roboto', sans-serif;
        font-weight: 500;
    }
    
    /* Enhanced AI Chat Interface */
    .chat-container {
        background: rgba(255, 255, 255, 0.35);
        backdrop-filter: blur(30px);
        border: 2px solid rgba(215, 53, 39, 0.25);
        border-radius: 25px;
        padding: clamp(1.5rem, 4vw, 3rem);
        min-height: clamp(400px, 60vh, 700px);
        position: relative;
        box-shadow: 0 20px 60px rgba(215, 53, 39, 0.1);
    }
    
    /* AI Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(215, 53, 39, 0.2) !important;
        border-radius: 15px !important;
        margin: 0.8rem 0 !important;
        padding: 1.2rem !important;
        box-shadow: 0 4px 15px rgba(215, 53, 39, 0.08) !important;
    }
    
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, rgba(215, 53, 39, 0.15), rgba(244, 162, 97, 0.15)) !important;
        border-color: rgba(215, 53, 39, 0.3) !important;
        margin-left: 10% !important;
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(248, 248, 248, 0.5)) !important;
        border-color: rgba(139, 90, 60, 0.3) !important;
        margin-right: 10% !important;
    }
    
    /* Chat Input Styling */
    .stChatInput > div > div > div {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        border: 2px solid rgba(215, 53, 39, 0.3) !important;
        border-radius: 15px !important;
        font-family: 'Roboto', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        color: #8b5a3c !important;
    }
    
    .stChatInput > div > div > div:focus {
        border-color: rgba(215, 53, 39, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(215, 53, 39, 0.1) !important;
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(135deg, 
            rgba(215, 53, 39, 0.9) 0%, 
            rgba(231, 111, 81, 0.9) 30%, 
            rgba(244, 162, 97, 0.9) 70%, 
            rgba(218, 165, 32, 0.9) 100%
        );
        backdrop-filter: blur(15px);
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        color: white;
        font-weight: 700;
        font-family: 'Roboto', sans-serif;
        padding: clamp(0.8rem, 2vw, 1.2rem) clamp(1.5rem, 4vw, 3rem);
        transition: all 0.4s ease;
        box-shadow: 0 8px 25px rgba(215, 53, 39, 0.25);
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        font-size: clamp(0.9rem, 2vw, 1.1rem);
        letter-spacing: 0.5px;
        text-transform: uppercase;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 15px 40px rgba(215, 53, 39, 0.35);
        background: linear-gradient(135deg, 
            rgba(183, 45, 33, 0.95) 0%, 
            rgba(207, 100, 73, 0.95) 30%, 
            rgba(220, 146, 87, 0.95) 70%, 
            rgba(184, 140, 27, 0.95) 100%
        );
    }
    
    /* Enhanced Form Elements */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input {
        background: rgba(255, 255, 255, 0.35) !important;
        backdrop-filter: blur(15px) !important;
        border: 2px solid rgba(215, 53, 39, 0.25) !important;
        border-radius: 10px !important;
        color: #8b5a3c !important;
        font-family: 'Roboto', sans-serif !important;
        font-weight: 500 !important;
        font-size: clamp(0.9rem, 2vw, 1.1rem) !important;
        padding: clamp(0.6rem, 2vw, 1rem) !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stDateInput > div > div > input:focus,
    .stTimeInput > div > div > input:focus {
        border-color: rgba(215, 53, 39, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(215, 53, 39, 0.1) !important;
        transform: scale(1.01) !important;
    }
    
    /* Enhanced Metrics */
    .metric-card {
        background: rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(20px);
        border: 2px solid rgba(215, 53, 39, 0.25);
        border-radius: 18px;
        padding: clamp(1.2rem, 3vw, 2.5rem);
        text-align: center;
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(215, 53, 39, 0.1);
    }
    
    .metric-card:hover {
        transform: translateY(-6px) scale(1.03);
        box-shadow: 0 20px 50px rgba(215, 53, 39, 0.2);
        border-color: rgba(215, 53, 39, 0.4);
    }
    
    .metric-value {
        font-family: 'Playfair Display', serif;
        font-size: clamp(2rem, 5vw, 3.2rem);
        font-weight: 800;
        color: #d73527;
        margin-bottom: 0.8rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    
    .metric-label {
        color: rgba(139, 90, 60, 0.8);
        font-size: clamp(0.8rem, 2vw, 1.1rem);
        font-weight: 600;
        font-family: 'Roboto', sans-serif;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    
    /* Success/Error Messages */
    .success-message {
        background: rgba(76, 175, 80, 0.25);
        backdrop-filter: blur(15px);
        border: 2px solid rgba(76, 175, 80, 0.4);
        border-radius: 15px;
        padding: clamp(1rem, 3vw, 2rem);
        color: #1b5e20;
        margin: clamp(1rem, 2vw, 2rem) 0;
        font-family: 'Roboto', sans-serif;
        font-weight: 600;
        font-size: clamp(1rem, 2vw, 1.2rem);
        box-shadow: 0 8px 25px rgba(76, 175, 80, 0.15);
    }
    
    .error-message {
        background: rgba(255, 87, 34, 0.25);
        backdrop-filter: blur(15px);
        border: 2px solid rgba(255, 87, 34, 0.4);
        border-radius: 15px;
        padding: clamp(1rem, 3vw, 2rem);
        color: #bf360c;
        margin: clamp(1rem, 2vw, 2rem) 0;
        font-family: 'Roboto', sans-serif;
        font-weight: 600;
        font-size: clamp(1rem, 2vw, 1.2rem);
        box-shadow: 0 8px 25px rgba(255, 87, 34, 0.15);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .nav-header { 
            padding: 1.2rem 1.5rem; 
            margin-bottom: 2rem;
        }
        .glass-card { 
            padding: 1.5rem; 
            margin: 1rem 0; 
            border-radius: 15px;
        }
        .restaurant-card { 
            padding: 1.2rem; 
            margin: 1rem 0;
            border-radius: 15px;
        }
        .chat-container {
            padding: 1.5rem;
            min-height: 400px;
            border-radius: 20px;
        }
        .stChatMessage {
            margin: 0.5rem 0 !important;
            padding: 1rem !important;
            border-radius: 12px !important;
        }
        .stChatMessage[data-testid="user-message"] {
            margin-left: 5% !important;
        }
        .stChatMessage[data-testid="assistant-message"] {
            margin-right: 5% !important;
        }
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    .status-online {
        background: rgba(76, 175, 80, 0.2);
        color: #2e7d32;
        border: 1px solid rgba(76, 175, 80, 0.4);
    }
    
    .status-offline {
        background: rgba(244, 67, 54, 0.2);
        color: #c62828;
        border: 1px solid rgba(244, 67, 54, 0.4);
    }
    
    .status-warning {
        background: rgba(255, 152, 0, 0.2);
        color: #ef6c00;
        border: 1px solid rgba(255, 152, 0, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Enhanced session state initialization with AI agent compatibility
def initialize_session_state():
    """Initialize session state with AI agent compatibility"""
    default_states = {
        'messages': [{"role": "assistant", "content": "Welcome to FoodieSpot! I'm your AI dining concierge ready to help you discover exceptional culinary experiences. What type of cuisine are you craving today?"}],
        'restaurants': [],
        'selected_restaurant': None,
        'current_page': "Home",
        'search_filters': {},
        'booking_data': {},
        'last_api_call': None,
        'last_cuisine_search': None,
        'last_city_search': None,
        'ai_agent_ready': False,
        'conversation_context': [],
        'system_status': None,
        'cached_restaurants': None
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Check AI agent availability
    try:
        if ai_agent is not None:
            st.session_state.ai_agent_ready = True
            logger.info("AI agent is ready and connected to Supabase")
        else:
            st.session_state.ai_agent_ready = False
            logger.warning("AI agent not available, using fallback mode")
    except Exception as e:
        st.session_state.ai_agent_ready = False
        logger.error(f"Error checking AI agent: {e}")

# Enhanced API functions with better error handling
def make_api_request(endpoint, method="GET", data=None):
    """Make API requests with enhanced error handling and caching"""
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        logger.info(f"Making {method} request to {url}")
        
        # Simple caching mechanism
        cache_key = f"{method}_{endpoint}_{str(data)}"
        if cache_key == st.session_state.get('last_api_call'):
            return st.session_state.get('last_api_result')
        
        if method == "GET":
            response = requests.get(url, timeout=15)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=15)
        
        if response.status_code in [200, 201]:
            result = response.json()
            st.session_state['last_api_call'] = cache_key
            st.session_state['last_api_result'] = result
            return result
        else:
            logger.error(f"API Error: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to API")
        return None
    except requests.exceptions.Timeout:
        logger.error("API request timeout")
        return None
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        return None

def get_restaurants_from_api():
    """Get restaurants with caching"""
    if st.session_state.cached_restaurants is None:
        result = make_api_request("restaurants")
        if result and result.get('success'):
            st.session_state.cached_restaurants = result['data']
            return result['data']
        return []
    return st.session_state.cached_restaurants

# Enhanced AI agent processing with full Supabase integration
def process_user_input_with_ai(user_input: str):
    """Enhanced AI agent processing with Supabase integration"""
    try:
        if not st.session_state.ai_agent_ready or ai_agent is None:
            return handle_fallback_response(user_input)
        
        # Use the AI agent with full tool integration
        response = ai_agent.chat(user_input)
        
        # Update session state with any restaurant data from AI agent
        if hasattr(ai_agent, 'last_search_results') and ai_agent.last_search_results:
            st.session_state.restaurants = ai_agent.last_search_results[:10]
        
        return response
        
    except Exception as e:
        logger.error(f"AI agent error: {e}")
        return handle_fallback_response(user_input)

# Enhanced fallback response handler
def handle_fallback_response(user_input):
    """Fallback response handler when AI agent fails"""
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ['find', 'search', 'restaurant', 'food', 'cuisine']):
        return handle_restaurant_search(user_input)
    elif any(word in user_input_lower for word in ['book', 'reserve', 'table']):
        return "I'd be delighted to help you secure a table! Please navigate to our 'Reserve Table' section to complete your booking with our streamlined reservation system."
    elif any(word in user_input_lower for word in ['recommend', 'suggest', 'best']):
        return handle_recommendation_request(user_input)
    elif any(word in user_input_lower for word in ['status', 'health', 'system']):
        return check_system_status_text()
    else:
        return "I'm here to enhance your dining journey! I can help you discover exceptional restaurants, make seamless reservations, or provide personalized recommendations based on your preferences. What culinary adventure shall we plan today?"

def handle_restaurant_search(user_input):
    """Handle restaurant search with fallback"""
    cuisines = ['italian', 'mexican', 'chinese', 'japanese', 'french', 'indian', 'thai', 'american']
    found_cuisine = None
    
    for cuisine in cuisines:
        if cuisine in user_input.lower():
            found_cuisine = cuisine.title()
            st.session_state['last_cuisine_search'] = found_cuisine
            break
    
    if found_cuisine:
        endpoint = f"restaurants?cuisine={found_cuisine}"
        result = make_api_request(endpoint)
        
        if result and result.get('success'):
            st.session_state.restaurants = result['data'][:10]
            return f"Excellent choice! I've discovered {len(result['data'])} exceptional {found_cuisine} restaurants for you. Please visit our 'Discover' section to explore these carefully curated culinary options with detailed information and real-time availability."
    
    return "I'd be happy to help you find the perfect restaurant! Try asking for specific cuisines like Italian, Japanese, French, or any other preference you have in mind. I can also help you filter by location, price range, or special dietary requirements."

def handle_recommendation_request(user_input):
    """Handle recommendation requests"""
    try:
        if st.session_state.ai_agent_ready and ai_agent:
            # Use AI agent for recommendations
            response = ai_agent.chat(f"Give me restaurant recommendations based on: {user_input}")
            return response
        else:
            # Fallback to API recommendations
            preferences = {
                'cuisine': st.session_state.get('last_cuisine_search'),
                'city': st.session_state.get('last_city_search'),
                'min_rating': 4.0
            }
            
            result = make_api_request("recommendations", "POST", preferences)
            if result and result.get('success'):
                restaurants = result['data'][:5]
                st.session_state.restaurants = restaurants
                return f"Here are my top recommendations based on your preferences! I found {len(restaurants)} excellent options for you."
            else:
                return "I'm having trouble generating recommendations right now. Please try browsing our restaurant collection."
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        return "I'm having trouble generating recommendations right now. Please try browsing our restaurant collection."

def check_system_status_text():
    """Get system status as text"""
    try:
        status_info = {
            'ai_agent_available': st.session_state.ai_agent_ready,
            'api_available': False,
            'database_available': False
        }
        
        # Check API status
        api_result = make_api_request("health")
        if api_result:
            status_info['api_available'] = True
        
        # Check AI agent status
        if ai_agent:
            ai_status = ai_agent.get_status()
            status_info.update({
                'database_available': ai_status.get('database_initialized', False),
                'total_restaurants': ai_status.get('database_stats', {}).get('restaurants', 0),
                'total_reservations': ai_status.get('database_stats', {}).get('reservations', 0)
            })
        
        status_text = "🔍 **System Status:**\n\n"
        status_text += f"• AI Agent: {'🟢 Online' if status_info['ai_agent_available'] else '🔴 Offline'}\n"
        status_text += f"• API Service: {'🟢 Online' if status_info['api_available'] else '🔴 Offline'}\n"
        status_text += f"• Database: {'🟢 Connected' if status_info['database_available'] else '🔴 Disconnected'}\n"
        
        if status_info.get('total_restaurants'):
            status_text += f"• Restaurants: {status_info['total_restaurants']}\n"
            status_text += f"• Reservations: {status_info['total_reservations']}\n"
        
        return status_text
        
    except Exception as e:
        return f"Error checking system status: {str(e)}"

# Enhanced reservation handling with AI agent
def handle_reservation_with_ai(reservation_data):
    """Handle reservations through AI agent with Supabase integration"""
    try:
        if st.session_state.ai_agent_ready and ai_agent:
            # Format reservation request for AI agent
            reservation_text = f"""
            I want to make a reservation:
            - Restaurant: {reservation_data['restaurant_name']}
            - Customer: {reservation_data['customer_name']}
            - Email: {reservation_data['customer_email']}
            - Party size: {reservation_data['party_size']}
            - Date: {reservation_data['reservation_date']}
            - Time: {reservation_data['reservation_time']}
            - Special requests: {reservation_data.get('special_requests', 'None')}
            """
            
            response = ai_agent.chat(reservation_text)
            return response
        else:
            # Fallback to direct API call
            return make_api_request("reservations", "POST", reservation_data)
            
    except Exception as e:
        logger.error(f"Reservation error: {e}")
        return None

# Initialize session state
initialize_session_state()

# Navigation Header
st.markdown("""
<div class="nav-header">
    <h1 class="nav-title">FoodieSpot</h1>
    <p class="nav-subtitle">Premium AI-Powered Dining Experiences</p>
</div>
""", unsafe_allow_html=True)

# Navigation Tabs with proper state management
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🏠 Home", key="nav_home", use_container_width=True):
        st.session_state.current_page = "Home"
        st.rerun()

with col2:
    if st.button("🤖 AI Concierge", key="nav_chat", use_container_width=True):
        st.session_state.current_page = "Chat"
        st.rerun()

with col3:
    if st.button("📋 Reserve Table", key="nav_book", use_container_width=True):
        st.session_state.current_page = "Booking"
        st.rerun()

with col4:
    if st.button("🔍 Discover", key="nav_discover", use_container_width=True):
        st.session_state.current_page = "Discover"
        st.rerun()

# Main content based on current page
if st.session_state.current_page == "Home":
    # Hero Section
    st.markdown("""
    <div class="glass-card">
        <div style="text-align: center;">
            <h2 style="font-family: 'Playfair Display', serif; color: #8b5a3c; margin-bottom: 1rem;">
                Elevate Your Dining Experience
            </h2>
            <p style="color: rgba(139, 90, 60, 0.8); line-height: 1.6; max-width: 600px; margin: 0 auto; font-weight: 500;">
                Discover exceptional restaurants, make seamless reservations, and enjoy personalized recommendations 
                powered by advanced AI technology designed for food enthusiasts.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # System Status Display
    if st.session_state.ai_agent_ready:
        st.markdown('<div class="status-indicator status-online">🤖 AI Agent Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-indicator status-warning">⚠️ AI Agent Offline - Using Fallback Mode</div>', unsafe_allow_html=True)
    
    # Stats Section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">150+</div>
            <div class="metric-label">Premium Restaurants</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">50K+</div>
            <div class="metric-label">Satisfied Diners</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">4.9★</div>
            <div class="metric-label">Average Rating</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">24/7</div>
            <div class="metric-label">AI Assistance</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Featured Restaurants
    st.markdown("""
    <div class="glass-card">
        <h3 style="font-family: 'Playfair Display', serif; color: #8b5a3c; text-align: center; margin-bottom: 2rem;">
            Featured Culinary Destinations
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    restaurants = get_restaurants_from_api()[:6]
    
    if restaurants:
        for i in range(0, len(restaurants), 3):
            cols = st.columns(3)
            for j, restaurant in enumerate(restaurants[i:i+3]):
                with cols[j]:
                    st.markdown(f"""
                    <div class="restaurant-card">
                        <div style="text-align: center; font-size: 3.5rem; margin-bottom: 1rem;">🍽️</div>
                        <div class="restaurant-name">{restaurant['name']}</div>
                        <div class="restaurant-details">
                            <p><strong>Cuisine:</strong> {restaurant['cuisine']}</p>
                            <p><strong>Rating:</strong> ⭐ {restaurant['rating']}/5</p>
                            <p><strong>Price:</strong> {restaurant['price_range']}</p>
                            <p><strong>Location:</strong> {restaurant['city']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Reserve Now", key=f"home_book_{i}_{j}", use_container_width=True):
                        st.session_state.selected_restaurant = restaurant
                        st.session_state.current_page = "Booking"
                        st.rerun()
    else:
        st.markdown("""
        <div class="glass-card">
            <p style="text-align: center; color: rgba(139, 90, 60, 0.7); font-weight: 500;">
                Connect to our reservation system to view featured restaurants
            </p>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.current_page == "Chat":
    
    # Chat header with status
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 🤖 Your Personal Dining Concierge")
        st.markdown("*Powered by AI with real-time restaurant data*")
    
    
    
    with col2:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.messages = [st.session_state.messages[0]]  # Keep welcome message
            if ai_agent:
                ai_agent.reset_conversation()
            st.rerun()
    
    
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Enhanced chat input with suggestions
    st.markdown("#### 💡 Try asking:")
    suggestion_cols = st.columns(4)
    
    suggestions = [
        "Find Italian restaurants in New York",
        "Book a table for 2 tonight",
        "Recommend dinner spots",
        "Show me budget-friendly options"
    ]
    
    for i, suggestion in enumerate(suggestions):
        with suggestion_cols[i]:
            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": suggestion})
                
                with st.chat_message("assistant"):
                    with st.spinner("🤖 Processing your request..."):
                        response = process_user_input_with_ai(suggestion)
                        st.markdown(response)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
    
    # Main chat input
    if prompt := st.chat_input("Ask me about restaurants, make reservations, or get personalized recommendations..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Process with AI agent
        with st.chat_message("assistant"):
            with st.spinner("🤖 AI is analyzing your request..."):
                response = process_user_input_with_ai(prompt)
                st.markdown(response)
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == "Booking":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Reserve Your Perfect Table")
    
    # Get restaurants from AI agent or API
    restaurants = []
    if st.session_state.ai_agent_ready and ai_agent:
        try:
            # Use AI agent to get restaurants
            ai_response = ai_agent.chat("Show me all available restaurants")
            if hasattr(ai_agent, 'last_search_results'):
                restaurants = ai_agent.last_search_results
        except Exception as e:
            logger.error(f"Error getting restaurants from AI: {e}")
    
    # Fallback to API
    if not restaurants:
        restaurants = get_restaurants_from_api()
    
    restaurant_options = [r['name'] for r in restaurants] if restaurants else ["No restaurants available"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Restaurant Details")
        selected_restaurant_name = st.selectbox("🏪 Choose Restaurant", restaurant_options, key="restaurant_select")
        
        reservation_date = st.date_input(
            "📅 Reservation Date",
            min_value=date.today(),
            max_value=date.today() + timedelta(days=60),
            key="reservation_date"
        )
        
        reservation_time = st.time_input(
            "🕐 Preferred Time", 
            value=datetime.now().replace(hour=19, minute=0, second=0, microsecond=0).time(),
            key="reservation_time"
        )
    
    with col2:
        st.markdown("#### Guest Information")
        party_size = st.number_input("👥 Party Size", min_value=1, max_value=20, value=2, key="party_size")
        user_name = st.text_input("👤 Full Name", placeholder="Enter your full name", key="user_name")
        user_email = st.text_input("📧 Email Address", placeholder="your.email@example.com", key="user_email")
    
    special_requests = st.text_area(
        "📝 Special Requests", 
        placeholder="Dietary restrictions, seating preferences, special occasions...",
        key="special_requests"
    )
    
    # Check availability and reservation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔍 Check Availability", use_container_width=True, key="check_availability"):
            if selected_restaurant_name != "No restaurants available":
                selected_restaurant = next((r for r in restaurants if r['name'] == selected_restaurant_name), None)
                
                if selected_restaurant and st.session_state.ai_agent_ready and ai_agent:
                    # Use AI agent to check availability
                    availability_query = f"Check availability for {selected_restaurant_name} on {reservation_date} at {reservation_time} for {party_size} people"
                    response = ai_agent.chat(availability_query)
                    st.info(response)
                else:
                    # Fallback to API
                    availability_data = {
                        "restaurant_id": selected_restaurant['id'],
                        "date": reservation_date.isoformat(),
                        "time": reservation_time.strftime("%H:%M"),
                        "party_size": party_size
                    }
                    result = make_api_request("availability", "POST", availability_data)
                    if result and result.get('success'):
                        if result.get('available'):
                            st.success(f"✅ Available! {result.get('available_seats', 0)} seats remaining")
                        else:
                            st.warning(f"❌ Not available. Only {result.get('available_seats', 0)} seats remaining")
    
    with col2:
        if st.button("🎯 Confirm Reservation", use_container_width=True, key="confirm_reservation"):
            if user_name and user_email and restaurants and selected_restaurant_name != "No restaurants available":
                selected_restaurant = next((r for r in restaurants if r['name'] == selected_restaurant_name), None)
                
                if selected_restaurant:
                    reservation_data = {
                        "restaurant_name": selected_restaurant['name'],
                        "customer_name": user_name,
                        "customer_email": user_email,
                        "party_size": party_size,
                        "reservation_date": reservation_date.isoformat(),
                        "reservation_time": reservation_time.strftime("%H:%M"),
                        "special_requests": special_requests
                    }
                    
                    with st.spinner("🤖 AI is processing your reservation..."):
                        if st.session_state.ai_agent_ready and ai_agent:
                            # Use AI agent for reservation
                            response = handle_reservation_with_ai(reservation_data)
                            
                            if "confirmed" in response.lower() or "success" in response.lower():
                                st.markdown("""
                                <div class="success-message">
                                    🎉 <strong>Reservation Confirmed!</strong><br>
                                    Your table has been successfully reserved. A confirmation email will be sent shortly.
                                </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                            else:
                                st.markdown("""
                                <div class="error-message">
                                    ❌ <strong>Reservation Failed</strong><br>
                                    We couldn't process your reservation. Please try again or contact us directly.
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            # Fallback to direct API
                            api_reservation_data = {
                                "restaurant_id": selected_restaurant['id'],
                                "user_name": user_name,
                                "user_email": user_email,
                                "party_size": party_size,
                                "date": reservation_date.isoformat(),
                                "time": reservation_time.strftime("%H:%M"),
                                "special_requests": special_requests
                            }
                            result = make_api_request("reservations", "POST", api_reservation_data)
                            if result and result.get('success'):
                                st.markdown("""
                                <div class="success-message">
                                    🎉 <strong>Reservation Confirmed!</strong><br>
                                    Your table has been successfully reserved. A confirmation email will be sent shortly.
                                </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                            else:
                                st.markdown("""
                                <div class="error-message">
                                    ❌ <strong>Reservation Failed</strong><br>
                                    We couldn't process your reservation. Please try again or contact us directly.
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="error-message">
                    ⚠️ <strong>Missing Information</strong><br>
                    Please fill in all required fields to complete your reservation.
                </div>
                """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🤖 Ask AI for Help", use_container_width=True, key="ai_help"):
            if st.session_state.ai_agent_ready and ai_agent:
                help_response = ai_agent.chat("Help me make a reservation. What information do you need?")
                st.info(help_response)
            else:
                st.info("AI assistant is not available. Please fill out the form manually.")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == "Discover":
    st.markdown("### 🔍 Discover Exceptional Restaurants")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cuisine_filter = st.selectbox("🍽️ Cuisine", ["All Cuisines", "Italian", "Japanese", "French", "Indian", "Chinese", "Mexican", "American", "Thai"], key="cuisine_filter")
    
    with col2:
        price_filter = st.selectbox("💰 Price Range", ["Any Budget", "$", "$$", "$$$", "$$$$"], key="price_filter")
    
    with col3:
        rating_filter = st.slider("⭐ Minimum Rating", 1.0, 5.0, 4.0, 0.1, key="rating_filter")
    
    with col4:
        city_filter = st.selectbox("📍 Location", ["All Cities", "New York", "Los Angeles", "Chicago", "San Francisco", "Miami"], key="city_filter")
    
    # Search and AI Recommendations
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Search Restaurants", use_container_width=True, key="search_restaurants"):
            params = []
            if cuisine_filter != "All Cuisines":
                params.append(f"cuisine={cuisine_filter}")
                st.session_state['last_cuisine_search'] = cuisine_filter
            if price_filter != "Any Budget":
                params.append(f"price_range={price_filter}")
            if city_filter != "All Cities":
                params.append(f"city={city_filter}")
                st.session_state['last_city_search'] = city_filter
            params.append(f"min_rating={rating_filter}")
            
            endpoint = f"restaurants?{'&'.join(params)}"
            result = make_api_request(endpoint)
            
            if result and result.get('success'):
                st.session_state.restaurants = result['data']
                st.success(f"Found {len(result['data'])} restaurants matching your criteria!")
            else:
                st.error("No restaurants found with these filters")
    
    with col2:
        if st.button("🤖 Get AI Recommendations", use_container_width=True, key="ai_recommendations"):
            if st.session_state.ai_agent_ready and ai_agent:
                # Use AI agent for smart recommendations
                preferences = {
                    'cuisine': cuisine_filter if cuisine_filter != "All Cuisines" else None,
                    'price_range': price_filter if price_filter != "Any Budget" else None,
                    'city': city_filter if city_filter != "All Cities" else None,
                    'min_rating': rating_filter
                }
                
                recommendation_query = f"Give me restaurant recommendations for {preferences}"
                response = ai_agent.chat(recommendation_query)
                st.info(response)
                
                if hasattr(ai_agent, 'last_search_results'):
                    st.session_state.restaurants = ai_agent.last_search_results
            else:
                st.warning("AI recommendations not available. Using search instead.")
    
    # Display restaurants
    if st.session_state.restaurants:
        st.markdown("### 🍽️ Restaurant Results")
        
        for restaurant in st.session_state.restaurants:
            st.markdown(f"""
            <div class="restaurant-card">
                <div style="text-align: center; font-size: 3rem; margin-bottom: 1rem;">🍽️</div>
                <div class="restaurant-name">{restaurant['name']}</div>
                <div class="restaurant-details">
                    <p><strong>Cuisine:</strong> {restaurant['cuisine']}</p>
                    <p><strong>Rating:</strong> ⭐ {restaurant['rating']}/5</p>
                    <p><strong>Price:</strong> {restaurant['price_range']}</p>
                    <p><strong>Location:</strong> {restaurant['city']}</p>
                    <p><strong>Phone:</strong> {restaurant.get('phone', 'N/A')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Reserve at {restaurant['name']}", key=f"discover_book_{restaurant['id']}", use_container_width=True):
                st.session_state.selected_restaurant = restaurant
                st.session_state.current_page = "Booking"
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 2rem; color: rgba(139, 90, 60, 0.6);">
    <p>© 2024 FoodieSpot - Premium AI-Powered Dining Experiences</p>
    <p>Powered by Advanced AI Technology & Supabase Database</p>
</div>
""", unsafe_allow_html=True)
