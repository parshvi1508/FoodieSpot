# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime, date, time

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Welcome to FoodieSpot AI Reservation API',
        'version': '1.0.0',
        'endpoints': {
            'restaurants': '/api/restaurants',
            'availability': '/api/availability',
            'reservations': '/api/reservations',
            'recommendations': '/api/recommendations',
            'health': '/api/health'
        }
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'FoodieSpot API is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/restaurants')
def get_restaurants():
    """Get restaurants with optional filtering"""
    try:
        # Extract query parameters
        cuisine = request.args.get('cuisine')
        city = request.args.get('city')
        price_range = request.args.get('price_range')
        min_rating = request.args.get('min_rating')
        
        # Build query
        query = supabase.table('restaurants').select('*')
        
        if cuisine:
            query = query.ilike('cuisine', f'%{cuisine}%')
        if city:
            query = query.ilike('city', f'%{city}%')
        if price_range:
            query = query.eq('price_range', price_range)
        if min_rating:
            query = query.gte('rating', float(min_rating))
        
        # Execute query
        response = query.order('rating', desc=True).execute()
        
        return jsonify({
            'success': True,
            'data': response.data,
            'count': len(response.data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/availability', methods=['POST'])
def check_availability():
    """Check restaurant availability"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['restaurant_id', 'date', 'time', 'party_size']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        restaurant_id = data['restaurant_id']
        date_str = data['date']
        time_str = data['time']
        party_size = int(data['party_size'])
        
        # Get restaurant capacity
        restaurant_response = supabase.table('restaurants').select('capacity').eq('id', restaurant_id).single().execute()
        
        if not restaurant_response.data:
            return jsonify({
                'success': False,
                'error': 'Restaurant not found'
            }), 404
        
        capacity = restaurant_response.data['capacity']
        
        # Check existing reservations
        reservations_response = supabase.table('reservations').select('party_size').eq(
            'restaurant_id', restaurant_id
        ).eq('reservation_date', date_str).eq('reservation_time', time_str).neq('status', 'cancelled').execute()
        
        # Calculate availability
        total_reserved = sum(r['party_size'] for r in reservations_response.data)
        available_capacity = capacity - total_reserved
        is_available = available_capacity >= party_size
        
        return jsonify({
            'success': True,
            'data': {
                'available': is_available,
                'capacity': capacity,
                'reserved': total_reserved,
                'available_capacity': available_capacity,
                'requested_party_size': party_size
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    """Create a new reservation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['restaurant_id', 'user_email', 'user_name', 'party_size', 'reservation_date', 'reservation_time']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Check availability first
        availability_data = {
            'restaurant_id': data['restaurant_id'],
            'date': data['reservation_date'],
            'time': data['reservation_time'],
            'party_size': data['party_size']
        }
        
        # Simulate availability check (you can call the actual function)
        # For now, assume it's available
        
        # Create reservation
        reservation_data = {
            'restaurant_id': data['restaurant_id'],
            'user_email': data['user_email'],
            'user_name': data['user_name'],
            'user_phone': data.get('user_phone'),
            'party_size': int(data['party_size']),
            'reservation_date': data['reservation_date'],
            'reservation_time': data['reservation_time'],
            'special_requests': data.get('special_requests'),
            'status': 'pending'
        }
        
        response = supabase.table('reservations').insert(reservation_data).execute()
        
        return jsonify({
            'success': True,
            'message': 'Reservation created successfully',
            'data': response.data[0]
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recommendations')
def get_recommendations():
    """Get restaurant recommendations"""
    try:
        cuisine = request.args.get('cuisine')
        city = request.args.get('city')
        budget = request.args.get('budget')
        
        # Build query for recommendations
        query = supabase.table('restaurants').select('*')
        
        if cuisine:
            query = query.ilike('cuisine', f'%{cuisine}%')
        if city:
            query = query.ilike('city', f'%{city}%')
        if budget:
            # Map budget to price range
            budget_map = {
                'low': '$',
                'moderate': '$$',
                'high': '$$$',
                'luxury': '$$$$'
            }
            if budget in budget_map:
                query = query.eq('price_range', budget_map[budget])
        
        # Get top-rated restaurants
        response = query.order('rating', desc=True).limit(10).execute()
        
        return jsonify({
            'success': True,
            'data': response.data,
            'count': len(response.data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
