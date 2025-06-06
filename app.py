import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client
from pydantic import BaseModel, field_validator, ValidationError, EmailStr
from datetime import datetime, date
import os
from dotenv import load_dotenv
# Add to app.py
from recommendation_engine import recommendation_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Supabase client
try:
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise

# Pydantic models for validation
class AvailabilityRequest(BaseModel):
    restaurant_id: str
    date: date
    time: str
    party_size: int

    @field_validator('date')
    @classmethod
    def date_not_in_past(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("Date cannot be in the past")
        return value

    @field_validator('party_size')
    @classmethod
    def party_size_range(cls, value: int) -> int:
        if not 1 <= value <= 20:
            raise ValueError("Party size must be between 1 and 20")
        return value

class ReservationRequest(AvailabilityRequest):
    user_email: EmailStr
    user_name: str

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint accessed")
    return jsonify({
        'success': True,
        'message': 'FoodieSpot API is running',
        'timestamp': datetime.now().isoformat()
    })

# Get restaurants with filters
@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    logger.info(f"GET /api/restaurants called with args: {request.args}")
    
    try:
        query = supabase.table('restaurants').select('*')
        filters_applied = {}
        
        # Add filters based on query parameters
        if 'cuisine' in request.args:
            cuisine = request.args['cuisine']
            query = query.ilike('cuisine', f"%{cuisine}%")
            filters_applied['cuisine'] = cuisine
            logger.debug(f"Applied cuisine filter: {cuisine}")
        
        if 'city' in request.args:
            city = request.args['city']
            query = query.ilike('city', f"%{city}%")
            filters_applied['city'] = city
            logger.debug(f"Applied city filter: {city}")
        
        if 'price_range' in request.args:
            price_range = request.args['price_range']
            query = query.eq('price_range', price_range)
            filters_applied['price_range'] = price_range
            logger.debug(f"Applied price_range filter: {price_range}")
        
        if 'min_rating' in request.args:
            try:
                min_rating = float(request.args['min_rating'])
                query = query.gte('rating', min_rating)
                filters_applied['min_rating'] = min_rating
                logger.debug(f"Applied min_rating filter: {min_rating}")
            except ValueError:
                logger.warning(f"Invalid min_rating format: {request.args['min_rating']}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid min_rating format'
                }), 400
        
        # Execute query with ordering
        result = query.order('rating', desc=True).execute()
        
        logger.info(f"Successfully retrieved {len(result.data)} restaurants with filters: {filters_applied}")
        
        return jsonify({
            'success': True,
            'data': result.data,
            'count': len(result.data),
            'filters_applied': filters_applied
        })
    
    except Exception as e:
        logger.error(f"Error retrieving restaurants: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve restaurants',
            'debug_info': str(e) if app.debug else None
        }), 500

# Check availability
@app.route('/api/availability', methods=['POST'])
def check_availability():
    logger.info("POST /api/availability called")
    
    try:
        # Validate request data
        request_data = request.get_json(force=True, silent=True)
        if not request_data:
            logger.warning("Empty request body received")
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        logger.debug(f"Availability request data: {request_data}")
        
        try:
            data = AvailabilityRequest(**request_data)
        except ValidationError as e:
            logger.warning(f"Validation error in availability request: {e.errors()}")
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': [{'field': str(err['loc'][0]), 'message': err['msg']} for err in e.errors()]
            }), 400
        
        # Get restaurant capacity
        logger.debug(f"Checking restaurant capacity for ID: {data.restaurant_id}")
        restaurant_result = supabase.table('restaurants')\
                           .select('capacity, name')\
                           .eq('id', data.restaurant_id)\
                           .execute()
        
        if not restaurant_result.data:
            logger.warning(f"Restaurant not found: {data.restaurant_id}")
            return jsonify({
                'success': False,
                'error': 'Restaurant not found'
            }), 404
        
        restaurant = restaurant_result.data[0]
        logger.debug(f"Found restaurant: {restaurant['name']} with capacity: {restaurant['capacity']}")
        
        # Get existing reservations for the same date and time
        logger.debug(f"Checking existing reservations for {data.date} at {data.time}")
        reservations = supabase.table('reservations')\
                      .select('party_size')\
                      .eq('restaurant_id', data.restaurant_id)\
                      .eq('reservation_date', data.date.isoformat())\
                      .eq('reservation_time', data.time)\
                      .execute().data
        
        # Calculate availability
        total_reserved = sum(r['party_size'] for r in reservations)
        available_capacity = restaurant['capacity'] - total_reserved
        is_available = available_capacity >= data.party_size
        
        logger.info(f"Availability check result - Restaurant: {restaurant['name']}, "
                   f"Total capacity: {restaurant['capacity']}, Reserved: {total_reserved}, "
                   f"Available: {available_capacity}, Requested: {data.party_size}, "
                   f"Can accommodate: {is_available}")
        
        return jsonify({
            'success': True,
            'data': {
                'available': is_available,
                'capacity': restaurant['capacity'],
                'reserved': total_reserved,
                'available_capacity': available_capacity,
                'requested_party_size': data.party_size
            }
        })
    
    except Exception as e:
        logger.error(f"Unexpected error in availability check: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to check availability',
            'debug_info': str(e) if app.debug else None
        }), 500

# Create reservation
@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    logger.info("POST /api/reservations called")
    
    try:
        # Validate request data
        request_data = request.get_json(force=True, silent=True)
        if not request_data:
            logger.warning("Empty request body received for reservation")
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        logger.debug(f"Reservation request data: {request_data}")
        
        try:
            data = ReservationRequest(**request_data)
        except ValidationError as e:
            logger.warning(f"Validation error in reservation request: {e.errors()}")
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': [{'field': str(err['loc'][0]), 'message': err['msg']} for err in e.errors()]
            }), 400
        
        # Check restaurant exists and get capacity
        logger.debug(f"Verifying restaurant exists: {data.restaurant_id}")
        restaurant_result = supabase.table('restaurants')\
                           .select('capacity, name')\
                           .eq('id', data.restaurant_id)\
                           .execute()
        
        if not restaurant_result.data:
            logger.warning(f"Restaurant not found for reservation: {data.restaurant_id}")
            return jsonify({
                'success': False,
                'error': 'Restaurant not found'
            }), 404
        
        restaurant = restaurant_result.data[0]
        
        # Check availability before creating reservation
        logger.debug(f"Checking availability before creating reservation")
        reservations = supabase.table('reservations')\
                      .select('party_size')\
                      .eq('restaurant_id', data.restaurant_id)\
                      .eq('reservation_date', data.date.isoformat())\
                      .eq('reservation_time', data.time)\
                      .execute().data
        
        total_reserved = sum(r['party_size'] for r in reservations)
        available_capacity = restaurant['capacity'] - total_reserved
        
        if available_capacity < data.party_size:
            logger.warning(f"Insufficient capacity for reservation - Available: {available_capacity}, "
                          f"Requested: {data.party_size}")
            return jsonify({
                'success': False,
                'error': f'No available capacity. Only {available_capacity} seats available.'
            }), 409
        
        # Create reservation
        reservation_data = {
            'restaurant_id': data.restaurant_id,
            'user_email': data.user_email,
            'user_name': data.user_name,
            'party_size': data.party_size,
            'reservation_date': data.date.isoformat(),
            'reservation_time': data.time
        }
        
        logger.debug(f"Creating reservation with data: {reservation_data}")
        result = supabase.table('reservations').insert(reservation_data).execute()
        
        if result.data:
            logger.info(f"Reservation created successfully for {data.user_name} at {restaurant['name']}")
            return jsonify({
                'success': True,
                'message': 'Reservation created successfully',
                'data': result.data[0]
            }), 201
        else:
            logger.error("Reservation creation failed - no data returned")
            return jsonify({
                'success': False,
                'error': 'Failed to create reservation'
            }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in reservation creation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create reservation',
            'debug_info': str(e) if app.debug else None
        }), 500

# Get recommendations

@app.route('/api/recommendations/smart', methods=['POST'])
def get_smart_recommendations():
    """Get intelligent recommendations based on session preferences"""
    try:
        preferences = request.get_json() or {}
        
        # Extract session preferences
        session_prefs = {
            'cuisine': preferences.get('cuisine'),
            'city': preferences.get('city'),
            'budget': preferences.get('budget'),
            'price_range': preferences.get('price_range'),
            'min_rating': preferences.get('min_rating', 4.0),
            'date': preferences.get('date'),
            'time': preferences.get('time'),
            'party_size': preferences.get('party_size', 2)
        }
        
        # Remove None values
        session_prefs = {k: v for k, v in session_prefs.items() if v is not None}
        
        # Get recommendations
        result = recommendation_engine.get_recommendations(session_prefs, limit=10)
        
        return jsonify({
            'success': True,
            'data': result['recommendations'],
            'meta': {
                'fallback_used': result['fallback_used'],
                'available_count': result.get('available_count', 0),
                'total_count': result.get('total_count', 0),
                'response_time': result['response_time'],
                'message': result['message']
            }
        })
    
    except Exception as e:
        logger.error(f"Error in smart recommendations: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate recommendations'
        }), 500

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    logger.info(f"GET /api/recommendations called with args: {request.args}")
    
    try:
        query = supabase.table('restaurants').select('*')
        filters_applied = {}
        
        # Apply filters if provided
        if 'cuisine' in request.args:
            cuisine = request.args['cuisine']
            query = query.ilike('cuisine', f"%{cuisine}%")
            filters_applied['cuisine'] = cuisine
        
        if 'city' in request.args:
            city = request.args['city']
            query = query.ilike('city', f"%{city}%")
            filters_applied['city'] = city
        
        if 'budget' in request.args:
            budget_map = {
                'low': '$',
                'moderate': '$$',
                'high': '$$$',
                'luxury': '$$$$'
            }
            budget = request.args['budget']
            price_range = budget_map.get(budget)
            if price_range:
                query = query.eq('price_range', price_range)
                filters_applied['budget'] = budget
                filters_applied['price_range'] = price_range
            else:
                logger.warning(f"Invalid budget parameter: {budget}")
        
        # Get top-rated restaurants
        result = query.order('rating', desc=True).limit(10).execute()
        
        logger.info(f"Retrieved {len(result.data)} recommendations with filters: {filters_applied}")
        
        return jsonify({
            'success': True,
            'data': result.data,
            'count': len(result.data),
            'filters_applied': filters_applied
        })
    
    except Exception as e:
        logger.error(f"Error retrieving recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve recommendations',
            'debug_info': str(e) if app.debug else None
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)