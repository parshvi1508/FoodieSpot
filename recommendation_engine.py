import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import requests

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self, api_base_url="http://localhost:5000/api"):
        self.api_base_url = api_base_url
        
        # Weight factors for scoring
        self.weights = {
            'rating': 2.0,
            'location_match': 3.0,
            'price_match': 1.5,
            'cuisine_match': 2.5,
            'availability': 4.0
        }
    
    def _fetch_restaurants(self, filters: Dict = None) -> List[Dict]:
        """Fetch restaurants from API with optional filters"""
        try:
            params = {}
            if filters:
                if filters.get('cuisine'):
                    params['cuisine'] = filters['cuisine']
                if filters.get('city'):
                    params['city'] = filters['city']
                if filters.get('price_range'):
                    params['price_range'] = filters['price_range']
                if filters.get('min_rating'):
                    params['min_rating'] = filters['min_rating']
            
            endpoint = "restaurants"
            if params:
                param_str = "&".join([f"{k}={v}" for k, v in params.items()])
                endpoint += f"?{param_str}"
            
            response = requests.get(f"{self.api_base_url}/{endpoint}", timeout=5)
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
        except Exception as e:
            logger.error(f"Error fetching restaurants: {e}")
            return []
    
    def _check_availability(self, restaurant_id: str, date_str: str, time_str: str, party_size: int) -> bool:
        """Check if restaurant has availability"""
        try:
            data = {
                "restaurant_id": restaurant_id,
                "date": date_str,
                "time": time_str,
                "party_size": party_size
            }
            response = requests.post(f"{self.api_base_url}/availability", json=data, timeout=3)
            if response.status_code == 200:
                result = response.json()
                return result.get('data', {}).get('available', False)
            return False
        except Exception as e:
            logger.error(f"Error checking availability for restaurant {restaurant_id}: {e}")
            return False
    
    def cuisine_based_matching(self, restaurants: List[Dict], preferred_cuisine: str) -> List[Dict]:
        """Filter and score restaurants by cuisine preference"""
        if not preferred_cuisine:
            return restaurants
        
        matched = []
        for restaurant in restaurants:
            if restaurant['cuisine'].lower() == preferred_cuisine.lower():
                matched.append(restaurant)
        
        # Sort by rating within cuisine
        matched.sort(key=lambda x: x['rating'], reverse=True)
        return matched
    
    def location_proximity_scoring(self, restaurants: List[Dict], preferred_city: str) -> List[Dict]:
        """Score restaurants based on location proximity"""
        if not preferred_city:
            return restaurants
        
        scored_restaurants = []
        for restaurant in restaurants:
            proximity_score = 1.0 if restaurant['city'].lower() == preferred_city.lower() else 0.3
            restaurant['proximity_score'] = proximity_score
            scored_restaurants.append(restaurant)
        
        return scored_restaurants
    
    def price_range_filtering(self, restaurants: List[Dict], budget_preference: str) -> List[Dict]:
        """Filter restaurants by price range with budget mapping"""
        budget_map = {
            'low': '$',
            'moderate': '$$',
            'high': '$$$',
            'luxury': '$$$$'
        }
        
        target_price = budget_map.get(budget_preference, budget_preference)
        
        if not target_price:
            return restaurants
        
        # Exact match first, then adjacent ranges
        exact_match = [r for r in restaurants if r['price_range'] == target_price]
        
        # If no exact matches, include adjacent price ranges
        if not exact_match:
            price_order = ['$', '$$', '$$$', '$$$$']
            try:
                target_idx = price_order.index(target_price)
                adjacent_ranges = []
                if target_idx > 0:
                    adjacent_ranges.append(price_order[target_idx - 1])
                if target_idx < len(price_order) - 1:
                    adjacent_ranges.append(price_order[target_idx + 1])
                
                adjacent_match = [r for r in restaurants if r['price_range'] in adjacent_ranges]
                return adjacent_match
            except ValueError:
                return restaurants
        
        return exact_match
    
    def availability_based_fallbacks(self, restaurants: List[Dict], session_preferences: Dict) -> Dict:
        """Handle fully booked scenarios with intelligent fallbacks"""
        available_restaurants = []
        unavailable_restaurants = []
        
        # Check availability for each restaurant
        date_str = session_preferences.get('date', date.today().isoformat())
        time_str = session_preferences.get('time', '19:00')
        party_size = session_preferences.get('party_size', 2)
        
        for restaurant in restaurants:
            is_available = self._check_availability(
                restaurant['id'], date_str, time_str, party_size
            )
            
            if is_available:
                available_restaurants.append(restaurant)
            else:
                unavailable_restaurants.append(restaurant)
        
        # Fallback strategies
        fallback_used = False
        recommendations = available_restaurants
        
        if not available_restaurants:
            fallback_used = True
            # Strategy 1: Suggest alternative times (mock implementation)
            recommendations = unavailable_restaurants[:5]
            
        elif len(available_restaurants) < 3:
            # Strategy 2: Mix available with highly-rated unavailable
            fallback_used = True
            top_unavailable = sorted(unavailable_restaurants, key=lambda x: x['rating'], reverse=True)[:2]
            recommendations = available_restaurants + top_unavailable
        
        return {
            'restaurants': recommendations,
            'fallback_used': fallback_used,
            'available_count': len(available_restaurants),
            'total_count': len(restaurants)
        }
    
    def calculate_recommendation_score(self, restaurant: Dict, preferences: Dict) -> float:
        """Calculate comprehensive recommendation score"""
        score = 0.0
        
        # Base rating score
        score += restaurant['rating'] * self.weights['rating']
        
        # Location proximity score
        if preferences.get('city'):
            proximity = restaurant.get('proximity_score', 0)
            score += proximity * self.weights['location_match']
        
        # Price range match
        if preferences.get('price_range') and restaurant['price_range'] == preferences['price_range']:
            score += self.weights['price_match']
        
        # Cuisine match
        if preferences.get('cuisine') and restaurant['cuisine'].lower() == preferences['cuisine'].lower():
            score += self.weights['cuisine_match']
        
        # Availability bonus (if checked)
        if restaurant.get('is_available', True):
            score += self.weights['availability']
        
        return score
    
    def get_recommendations(self, session_preferences: Dict, limit: int = 10) -> Dict:
        """Main recommendation function with <1s response time"""
        start_time = time.time()
        
        try:
            # Step 1: Fetch restaurants with basic filters
            restaurants = self._fetch_restaurants(session_preferences)
            
            if not restaurants:
                response_time = time.time() - start_time
                return {
                    'recommendations': [],
                    'fallback_used': False,
                    'response_time': response_time,
                    'message': 'No restaurants found'
                }
            
            # Step 2: Apply cuisine-based matching
            if session_preferences.get('cuisine'):
                restaurants = self.cuisine_based_matching(restaurants, session_preferences['cuisine'])
            
            # Step 3: Apply location proximity scoring
            if session_preferences.get('city'):
                restaurants = self.location_proximity_scoring(restaurants, session_preferences['city'])
            
            # Step 4: Apply price range filtering
            if session_preferences.get('budget') or session_preferences.get('price_range'):
                budget = session_preferences.get('budget') or session_preferences.get('price_range')
                restaurants = self.price_range_filtering(restaurants, budget)
            
            # Step 5: Check availability and apply fallbacks
            availability_result = self.availability_based_fallbacks(restaurants, session_preferences)
            restaurants = availability_result['restaurants']
            
            # Step 6: Calculate final scores and sort
            for restaurant in restaurants:
                restaurant['recommendation_score'] = self.calculate_recommendation_score(restaurant, session_preferences)
            
            restaurants.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            # Step 7: Limit results
            recommendations = restaurants[:limit]
            
            response_time = time.time() - start_time
            
            return {
                'recommendations': recommendations,
                'fallback_used': availability_result['fallback_used'],
                'available_count': availability_result['available_count'],
                'total_count': availability_result['total_count'],
                'response_time': response_time,
                'message': self._generate_recommendation_message(availability_result, len(recommendations))
            }
        
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Error generating recommendations: {e}")
            return {
                'recommendations': [],
                'fallback_used': False,
                'response_time': response_time,
                'message': 'Error generating recommendations'
            }
    
    def _generate_recommendation_message(self, availability_result: Dict, rec_count: int) -> str:
        """Generate user-friendly recommendation message"""
        if availability_result['fallback_used']:
            if availability_result['available_count'] == 0:
                return f"Found {rec_count} highly-rated restaurants. Some may be fully booked - we suggest calling ahead or trying different times."
            else:
                return f"Found {rec_count} restaurants including {availability_result['available_count']} with immediate availability."
        else:
            return f"Found {rec_count} available restaurants matching your preferences."

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()
