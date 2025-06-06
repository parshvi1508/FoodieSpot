import streamlit as st
import requests
import json
from datetime import datetime, date, timedelta
import pandas as pd
import logging
from ai_agent import ai_agent

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

# API Configuration
API_BASE_URL = "http://localhost:5000/api"

# Enhanced Responsive CSS with Professional Food Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;500;600;700;800&family=Roboto:wght@300;400;500;600;700&display=swap');
    
    /* Global Reset with Enhanced Food Colors */
    .stApp {
        background: linear-gradient(135deg, 
            rgba(215, 53, 39, 0.08) 0%,    /* Rich Tomato Red */
            rgba(244, 162, 97, 0.06) 20%,  /* Warm Paprika */
            rgba(139, 90, 60, 0.08) 40%,   /* Coffee Brown */
            rgba(205, 133, 63, 0.06) 60%,  /* Sandy Brown */
            rgba(160, 82, 45, 0.08) 80%,   /* Saddle Brown */
            rgba(218, 165, 32, 0.06) 100%  /* Goldenrod */
        );
        background-attachment: fixed;
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        color: #2c1810;
    }
    
    /* Enhanced Animated Background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 15% 85%, rgba(215, 53, 39, 0.12) 0%, transparent 45%),
            radial-gradient(circle at 85% 15%, rgba(244, 162, 97, 0.1) 0%, transparent 45%),
            radial-gradient(circle at 45% 45%, rgba(139, 90, 60, 0.08) 0%, transparent 45%),
            radial-gradient(circle at 70% 80%, rgba(218, 165, 32, 0.08) 0%, transparent 45%);
        z-index: -1;
        animation: foodieFlow 30s ease-in-out infinite;
    }
    
    @keyframes foodieFlow {
        0%, 100% { 
            transform: scale(1) rotate(0deg);
            opacity: 0.8;
        }
        25% { 
            transform: scale(1.02) rotate(0.3deg);
            opacity: 0.9;
        }
        50% { 
            transform: scale(1.04) rotate(0.6deg);
            opacity: 1;
        }
        75% { 
            transform: scale(1.01) rotate(-0.3deg);
            opacity: 0.85;
        }
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
        animation: headerFloat 8s ease-in-out infinite;
    }
    
    @keyframes headerFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-3px); }
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
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        animation: titleShimmer 6s ease-in-out infinite;
    }
    
    @keyframes titleShimmer {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.01); }
    }
    
    .nav-subtitle {
        text-align: center;
        color: rgba(139, 90, 60, 0.9);
        font-size: clamp(1rem, 2.5vw, 1.4rem);
        margin-top: 0.8rem;
        font-weight: 500;
        font-family: 'Roboto', sans-serif;
        letter-spacing: 0.5px;
        animation: subtitleGlow 4s ease-in-out infinite;
    }
    
    @keyframes subtitleGlow {
        0%, 100% { opacity: 0.8; }
        50% { opacity: 1; }
    }
    
    /* Enhanced Glass Cards - Responsive */
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
        animation: cardBreathe 12s ease-in-out infinite;
    }
    
    @keyframes cardBreathe {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-4px); }
    }
    
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(215, 53, 39, 0.6), 
            rgba(244, 162, 97, 0.6), 
            rgba(218, 165, 32, 0.6), 
            transparent
        );
        animation: borderFlow 4s ease-in-out infinite;
    }
    
    @keyframes borderFlow {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 0.8; }
    }
    
    .glass-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 25px 70px rgba(215, 53, 39, 0.15);
        border-color: rgba(215, 53, 39, 0.4);
    }
    
    /* Enhanced Restaurant Cards - Responsive */
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
        animation: cardPulse 15s ease-in-out infinite;
    }
    
    @keyframes cardPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.01); }
    }
    
    .restaurant-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #d73527, #e76f51, #f4a261, #daa520);
        animation: gradientShift 6s ease-in-out infinite;
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
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
        animation: nameGlow 8s ease-in-out infinite;
    }
    
    @keyframes nameGlow {
        0%, 100% { text-shadow: 1px 1px 3px rgba(139, 90, 60, 0.3); }
        50% { text-shadow: 2px 2px 6px rgba(139, 90, 60, 0.5); }
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
        animation: chatPulse 10s ease-in-out infinite;
        box-shadow: 0 20px 60px rgba(215, 53, 39, 0.1);
    }
    
    @keyframes chatPulse {
        0%, 100% { box-shadow: 0 20px 60px rgba(215, 53, 39, 0.1); }
        50% { box-shadow: 0 25px 70px rgba(215, 53, 39, 0.15); }
    }
    
    /* AI Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(215, 53, 39, 0.2) !important;
        border-radius: 15px !important;
        margin: 0.8rem 0 !important;
        padding: 1.2rem !important;
        animation: messageSlideIn 0.5s ease-out !important;
        box-shadow: 0 4px 15px rgba(215, 53, 39, 0.08) !important;
    }
    
    @keyframes messageSlideIn {
        from { 
            opacity: 0; 
            transform: translateY(20px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
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
    
    /* Booking Form Enhancement */
    .booking-form {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(30px);
        border: 2px solid rgba(215, 53, 39, 0.25);
        border-radius: 25px;
        padding: clamp(1.5rem, 4vw, 2.5rem);
        box-shadow: 0 20px 60px rgba(215, 53, 39, 0.12);
        animation: formFloat 12s ease-in-out infinite;
    }
    
    @keyframes formFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-3px); }
    }
    
    /* Enhanced Buttons - Responsive */
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
        animation: buttonGlow 8s ease-in-out infinite;
        width: 100%;
    }
    
    @keyframes buttonGlow {
        0%, 100% { box-shadow: 0 8px 25px rgba(215, 53, 39, 0.25); }
        50% { box-shadow: 0 12px 35px rgba(215, 53, 39, 0.4); }
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
    
    /* Enhanced Form Elements - Responsive */
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
    
    /* Enhanced Metrics - Responsive */
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
        animation: metricFloat 10s ease-in-out infinite;
        box-shadow: 0 10px 30px rgba(215, 53, 39, 0.1);
    }
    
    @keyframes metricFloat {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-3px) rotate(0.5deg); }
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
        animation: valueCount 5s ease-in-out infinite;
    }
    
    @keyframes valueCount {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .metric-label {
        color: rgba(139, 90, 60, 0.8);
        font-size: clamp(0.8rem, 2vw, 1.1rem);
        font-weight: 600;
        font-family: 'Roboto', sans-serif;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    
    /* Enhanced Typography - Responsive */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Playfair Display', serif;
        color: #8b5a3c;
        font-weight: 700;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    
    h2 { font-size: clamp(1.8rem, 4vw, 2.8rem); font-weight: 800; }
    h3 { font-size: clamp(1.4rem, 3vw, 2.2rem); font-weight: 700; }
    h4 { font-size: clamp(1.2rem, 2.5vw, 1.8rem); font-weight: 600; }
    
    p, span, div {
        font-family: 'Roboto', sans-serif;
        font-weight: 400;
        line-height: 1.6;
        font-size: clamp(0.9rem, 2vw, 1.1rem);
    }
    
    /* Enhanced Success/Error Messages - Responsive */
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
        animation: messageSlide 0.6s ease-out;
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
        animation: messageSlide 0.6s ease-out;
        box-shadow: 0 8px 25px rgba(255, 87, 34, 0.15);
    }
    
    @keyframes messageSlide {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Responsive Design Breakpoints */
    @media (max-width: 1200px) {
        .nav-header { padding: 1.5rem 2rem; }
        .glass-card { margin: 1.5rem 0; }
        .restaurant-card { margin: 1.5rem 0; }
    }
    
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
        .booking-form {
            padding: 1.5rem;
            border-radius: 20px;
        }
        .metric-card {
            padding: 1.5rem;
            border-radius: 15px;
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
    
    @media (max-width: 480px) {
        .nav-header { 
            padding: 1rem; 
            margin-bottom: 1.5rem;
            border-radius: 20px;
        }
        .glass-card { 
            padding: 1rem; 
            margin: 0.8rem 0;
            border-radius: 12px;
        }
        .restaurant-card { 
            padding: 1rem; 
            margin: 0.8rem 0;
            border-radius: 12px;
        }
        .chat-container {
            padding: 1rem;
            min-height: 350px;
            border-radius: 15px;
        }
        .booking-form {
            padding: 1rem;
            border-radius: 15px;
        }
        .metric-card {
            padding: 1rem;
            border-radius: 12px;
        }
        .stButton > button {
            padding: 0.8rem 1.5rem;
            font-size: 0.9rem;
            border-radius: 10px;
        }
        .stChatMessage {
            margin: 0.3rem 0 !important;
            padding: 0.8rem !important;
            border-radius: 10px !important;
        }
        .stChatMessage[data-testid="user-message"] {
            margin-left: 2% !important;
        }
        .stChatMessage[data-testid="assistant-message"] {
            margin-right: 2% !important;
        }
    }
    
    /* Loading and Interaction States */
    .loading-spinner {
        display: inline-block;
        width: 30px;
        height: 30px;
        border: 3px solid rgba(215, 53, 39, 0.3);
        border-radius: 50%;
        border-top-color: #d73527;
        animation: enhancedSpin 1.2s ease-in-out infinite;
    }
    
    @keyframes enhancedSpin {
        to { transform: rotate(360deg) scale(1.05); }
    }
    
    /* Accessibility Improvements */
    .stButton > button:focus,
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        outline: 3px solid rgba(215, 53, 39, 0.5);
        outline-offset: 2px;
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .glass-card {
            background: rgba(40, 40, 40, 0.4);
            border-color: rgba(215, 53, 39, 0.3);
        }
        .restaurant-card {
            background: rgba(50, 50, 50, 0.4);
            border-color: rgba(215, 53, 39, 0.3);
        }
        .chat-container {
            background: rgba(45, 45, 45, 0.4);
            border-color: rgba(215, 53, 39, 0.3);
        }
    }
</style>
""", unsafe_allow_html=True)

# Fixed session state initialization
def initialize_session_state():
    """Initialize session state with proper error handling"""
    default_states = {
        'messages': [{"role": "assistant", "content": "Welcome to FoodieSpot! I'm your AI dining concierge ready to help you discover exceptional culinary experiences. What type of cuisine are you craving today?"}],
        'restaurants': [],
        'selected_restaurant': None,
        'current_page': "Home",
        'search_filters': {},
        'booking_data': {},
        'last_api_call': None,
        'last_cuisine_search': None,
        'last_city_search': None
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# API functions with better error handling
def make_api_request(endpoint, method="GET", data=None):
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        logger.info(f"Making {method} request to {url}")
        
        cache_key = f"{method}_{endpoint}_{str(data)}"
        if cache_key == st.session_state.get('last_api_call'):
            return st.session_state.get('last_api_result')
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code in [200, 201]:
            result = response.json()
            st.session_state['last_api_call'] = cache_key
            st.session_state['last_api_result'] = result
            return result
        else:
            st.error(f"API Error: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("Unable to connect to our reservation system. Please ensure the backend service is running.")
        return None
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None

def get_restaurants_from_api():
    """Get restaurants with caching"""
    if 'cached_restaurants' not in st.session_state:
        result = make_api_request("restaurants")
        if result and result.get('success'):
            st.session_state['cached_restaurants'] = result['data']
            return result['data']
        return []
    return st.session_state['cached_restaurants']

# Add smart recommendations function
def get_smart_recommendations(preferences):
    """Get smart recommendations from the recommendation engine"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/recommendations/smart",
            json=preferences,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error getting recommendations: {e}")
        return None

# Update the handle_recommendation_request function
def handle_recommendation_request(user_input):
    """Enhanced recommendation handling"""
    # Extract preferences from session state or user input
    preferences = {
        'cuisine': st.session_state.get('last_cuisine_search'),
        'city': st.session_state.get('last_city_search'),
        'budget': 'moderate',  # Default
        'min_rating': 4.0,
        'party_size': 2
    }
    
    result = get_smart_recommendations(preferences)
    
    if result and result.get('success'):
        restaurants = result['data']
        meta = result['meta']
        
        st.session_state.restaurants = restaurants[:5]
        
        response_msg = f"{meta['message']} "
        if meta['response_time'] < 1.0:
            response_msg += f"(Found in {meta['response_time']:.3f}s)"
        
        return response_msg
    else:
        return "I'm having trouble generating recommendations right now. Please try again or browse our restaurant collection."

def process_user_input(user_input: str):
    # First check for AI agent response
    ai_response = ai_agent.chat(user_input)
    if ai_response and ai_response.strip():
        return ai_response
    
    # Fallback to rule-based responses
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ['find', 'search', 'restaurant', 'food', 'cuisine']):
        return handle_restaurant_search(user_input)
    elif any(word in user_input_lower for word in ['book', 'reserve', 'table']):
        return "I'd be delighted to help you secure a table! Please navigate to our 'Reserve Table' section to complete your booking with our streamlined reservation system."
    elif any(word in user_input_lower for word in ['recommend', 'suggest', 'best']):
        return handle_recommendation_request(user_input)
    else:
        return "I'm here to enhance your dining journey! I can help you discover exceptional restaurants, make seamless reservations, or provide personalized recommendations based on your preferences. What culinary adventure shall we plan today?"

def handle_restaurant_search(user_input):
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

# Initialize session state at the start
initialize_session_state()

# Navigation Header
st.markdown("""
<div class="nav-header">
    <h1 class="nav-title">FoodieSpot</h1>
    <p class="nav-subtitle">Premium AI-Powered Dining Experiences</p>
</div>
""", unsafe_allow_html=True)

# Fixed Navigation Tabs with proper state management
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
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown("### 🤖 Your Personal Dining Concierge")
    st.markdown("*Ask me anything about restaurants, cuisines, reservations, or dining recommendations*")
    
    # Display chat messages with enhanced styling
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Enhanced chat input with better UX
    if prompt := st.chat_input("Ask me about restaurants, cuisines, reservations, or get personalized recommendations..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Show typing indicator
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = process_user_input(prompt)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == "Booking":
    st.markdown('<div class="booking-form">', unsafe_allow_html=True)
    st.markdown("### 📋 Reserve Your Perfect Table")
    
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
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Confirm Reservation", use_container_width=True, key="confirm_reservation"):
            if user_name and user_email and restaurants:
                selected_restaurant = next((r for r in restaurants if r['name'] == selected_restaurant_name), None)
                
                if selected_restaurant:
                    with st.spinner("Processing your reservation..."):
                        reservation_data = {
                            "restaurant_id": selected_restaurant['id'],
                            "user_name": user_name,
                            "user_email": user_email,
                            "party_size": party_size,
                            "reservation_date": reservation_date.isoformat(),
                            "reservation_time": reservation_time.strftime("%H:%M"),
                            "special_requests": special_requests
                        }
                        
                        result = make_api_request("reservations", "POST", reservation_data)
                        
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
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == "Discover":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
    
    # Smart Recommendations Button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Search Restaurants", use_container_width=True, key="search_restaurants"):
            params = []
            if cuisine_filter != "All Cuisines":
                params.append(f"cuisine={cuisine_filter}")
                st.session_state['last_cuisine_search'] = cuisine_filter
            if price_filter != "Any Budget":
                params.append(f"price_range={price_filter}")
            if rating_filter > 1.0:
                params.append(f"min_rating={rating_filter}")
            if city_filter != "All Cities":
                params.append(f"city={city_filter}")
                st.session_state['last_city_search'] = city_filter
            
            endpoint = "restaurants"
            if params:
                endpoint += "?" + "&".join(params)
            
            with st.spinner("Discovering restaurants..."):
                result = make_api_request(endpoint)
                if result and result.get('success'):
                    st.session_state.restaurants = result['data']
                    st.rerun()
    
    with col2:
        if st.button("🎯 Smart Recommendations", use_container_width=True, key="smart_recommendations"):
            with st.spinner("Getting personalized recommendations..."):
                preferences = {
                    'cuisine': cuisine_filter if cuisine_filter != "All Cuisines" else None,
                    'city': city_filter if city_filter != "All Cities" else None,
                    'budget': price_filter if price_filter != "Any Budget" else 'moderate',
                    'min_rating': rating_filter,
                    'party_size': 2
                }
                
                result = get_smart_recommendations(preferences)
                if result and result.get('success'):
                    st.session_state.restaurants = result['data']
                    st.success(f"Found {len(result['data'])} personalized recommendations!")
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    restaurants_to_show = st.session_state.restaurants if st.session_state.restaurants else get_restaurants_from_api()
    
    if restaurants_to_show:
        st.markdown(f"### Found {len(restaurants_to_show)} Exceptional Restaurants")
        
        for i in range(0, len(restaurants_to_show), 3):
            cols = st.columns(3)
            for j, restaurant in enumerate(restaurants_to_show[i:i+3]):
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
                            <p><strong>Capacity:</strong> {restaurant['capacity']} seats</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Reserve Table", key=f"discover_book_{i}_{j}", use_container_width=True):
                        st.session_state.selected_restaurant = restaurant
                        st.session_state.current_page = "Booking"
                        st.rerun()
    else:
        # Professional Empty State
        st.markdown("""
        <div class="glass-card">
            <div class="empty-state-container" style="text-align: center; padding: 4rem 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1.5rem; opacity: 0.7;">🔍</div>
                <h3 style="font-family: 'Playfair Display', serif; color: #8b5a3c; margin-bottom: 1rem;">
                    Ready to Discover Your Perfect Dining Experience?
                </h3>
                <p style="color: rgba(139, 90, 60, 0.8); line-height: 1.6; max-width: 500px; margin-left: auto; margin-right: auto; margin-bottom: 2.5rem;">
                    Use the filters above to find restaurants that match your preferences, or let our AI assistant guide you to the perfect meal.
                </p>
                <div style="display: flex; gap: 1.5rem; justify-content: center; flex-wrap: wrap;">
                    <div style="text-align: center;">
                        <div style="background: linear-gradient(135deg, rgba(215, 53, 39, 0.1), rgba(244, 162, 97, 0.1)); border: 2px solid rgba(215, 53, 39, 0.3); border-radius: 15px; padding: 1.5rem; margin-bottom: 1rem; min-width: 200px;">
                            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🤖</div>
                            <h4 style="color: #8b5a3c; margin-bottom: 0.5rem; font-family: 'Playfair Display', serif;">AI Assistant</h4>
                            <p style="color: rgba(139, 90, 60, 0.7); font-size: 0.9rem;">Get personalized recommendations</p>
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="background: linear-gradient(135deg, rgba(215, 53, 39, 0.1), rgba(244, 162, 97, 0.1)); border: 2px solid rgba(215, 53, 39, 0.3); border-radius: 15px; padding: 1.5rem; margin-bottom: 1rem; min-width: 200px;">
                            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⭐</div>
                            <h4 style="color: #8b5a3c; margin-bottom: 0.5rem; font-family: 'Playfair Display', serif;">Top Rated</h4>
                            <p style="color: rgba(139, 90, 60, 0.7); font-size: 0.9rem;">Browse our highest-rated restaurants</p>
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="background: linear-gradient(135deg, rgba(215, 53, 39, 0.1), rgba(244, 162, 97, 0.1)); border: 2px solid rgba(215, 53, 39, 0.3); border-radius: 15px; padding: 1.5rem; margin-bottom: 1rem; min-width: 200px;">
                            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🍽️</div>
                            <h4 style="color: #8b5a3c; margin-bottom: 0.5rem; font-family: 'Playfair Display', serif;">All Cuisines</h4>
                            <p style="color: rgba(139, 90, 60, 0.7); font-size: 0.9rem;">Explore our complete collection</p>
                        </div>
                    </div>
                </div>
                <div style="margin-top: 2rem;">
                    <p style="color: rgba(139, 90, 60, 0.6); font-size: 1rem; font-style: italic;">
                        💡 Tip: Try filtering by cuisine, price range, or location to find exactly what you're craving
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Functional buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🤖 Ask AI Assistant", use_container_width=True, key="empty_ai"):
                st.session_state.current_page = "Chat"
                st.rerun()
        
        with col2:
            if st.button("⭐ View Top Rated", use_container_width=True, key="empty_top"):
                result = make_api_request("recommendations")
                if result and result.get('success'):
                    st.session_state.restaurants = result['data']
                    st.rerun()
        
        with col3:
            if st.button("🍽️ Show All Restaurants", use_container_width=True, key="empty_all"):
                restaurants = get_restaurants_from_api()
                if restaurants:
                    st.session_state.restaurants = restaurants
                    st.rerun()

# Footer
st.markdown("""
<div class="glass-card" style="margin-top: 3rem;">
    <div style="text-align: center; color: rgba(139, 90, 60, 0.7);">
        <p style="margin: 0; font-weight: 600;">🍽️ FoodieSpot AI - Where Every Meal Becomes a Memory</p>
        <p style="margin: 0.5rem 0 0 0;">© 2025 FoodieSpot Technologies | Premium Dining Experiences Powered by AI</p>
    </div>
</div>
""", unsafe_allow_html=True)