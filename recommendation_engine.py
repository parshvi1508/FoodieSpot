import time
import logging
from typing import Dict, List, Optional, Any
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Smart recommendation engine for FoodieSpot using only free resources.
    Provides intelligent restaurant recommendations based on user preferences,
    availability, and sophisticated scoring algorithms.
    """
    
    def __init__(self):
        """Initialize the recommendation engine with Supabase connection."""
        try:
            self.supabase = create_client(
                os.getenv("SUPABASE_URL"), 
                os.getenv("SUPABASE_ANON_KEY")
            )
            logger.info("Recommendation engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize recommendation engine: {e}")
            raise
    
    def get_recommendations(self, preferences: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
        """
        Get intelligent restaurant recommendations based on user preferences.
        
        Args:
            preferences: Dictionary containing user preferences
            limit: Maximum number of recommendations to return
            
        Returns:
            Dictionary containing recommendations and metadata
        """
        start_time = time.time()
        
        try:
            # Build base query
            query = self.supabase.table('restaurants').select('*')
            
            # Apply filters based on preferences
            query = self._apply_filters(query, preferences)
            
            # Execute query with ordering
            result = query.order('rating', desc=True).limit(limit * 2).execute()
            restaurants = result.data
            
            if not restaurants:
                # Fallback strategy
                return self._get_fallback_recommendations(preferences, limit, start_time)
            
            # Score and rank restaurants
            scored_restaurants = self._score_restaurants(restaurants, preferences)
            
            # Select top recommendations
            top_recommendations = scored_restaurants[:limit]
            
            response_time = time.time() - start_time
            
            return {
                'recommendations': top_recommendations,
                'fallback_used': False,
                'total_count': len(restaurants),
                'response_time': response_time,
                'message': self._generate_message(preferences, len(top_recommendations))
            }
            
        except Exception as e:
            logger.error(f"Error in get_recommendations: {e}")
            return self._get_fallback_recommendations(preferences, limit, start_time)
    
    def _apply_filters(self, query, preferences: Dict[str, Any]):
        """Apply user preference filters to the query."""
        
        # Cuisine filter with fuzzy matching
        if preferences.get('cuisine'):
            cuisine = preferences['cuisine']
            query = query.ilike('cuisine', f"%{cuisine}%")
            logger.debug(f"Applied cuisine filter: {cuisine}")
        
        # Location filter with city matching
        if preferences.get('city'):
            city = preferences['city']
            query = query.ilike('city', f"%{city}%")
            logger.debug(f"Applied city filter: {city}")
        
        # Price range filter with flexibility
        if preferences.get('price_range'):
            price_range = preferences['price_range']
            query = query.eq('price_range', price_range)
            logger.debug(f"Applied price_range filter: {price_range}")
        
        # Rating filter
        if preferences.get('min_rating'):
            min_rating = float(preferences['min_rating'])
            query = query.gte('rating', min_rating)
            logger.debug(f"Applied min_rating filter: {min_rating}")
        
        return query
    
    def _score_restaurants(self, restaurants: List[Dict], preferences: Dict[str, Any]) -> List[Dict]:
        """
        Score restaurants based on multiple factors and user preferences.
        
        Args:
            restaurants: List of restaurant data
            preferences: User preferences for scoring
            
        Returns:
            List of restaurants sorted by score (highest first)
        """
        scored_restaurants = []
        
        for restaurant in restaurants:
            score = self._calculate_restaurant_score(restaurant, preferences)
            restaurant['recommendation_score'] = score
            scored_restaurants.append(restaurant)
        
        # Sort by score (highest first)
        scored_restaurants.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return scored_restaurants
    
    def _calculate_restaurant_score(self, restaurant: Dict, preferences: Dict[str, Any]) -> float:
        """
        Calculate a comprehensive score for a restaurant based on multiple factors.
        
        Scoring factors:
        - Rating (40% weight)
        - Cuisine match (25% weight)
        - Price preference (20% weight)
        - Capacity/availability (15% weight)
        """
        score = 0.0
        
        # Rating score (40% weight) - normalized to 0-40
        rating = float(restaurant.get('rating', 0))
        score += (rating / 5.0) * 40
        
        # Cuisine match score (25% weight)
        if preferences.get('cuisine'):
            preferred_cuisine = preferences['cuisine'].lower()
            restaurant_cuisine = restaurant.get('cuisine', '').lower()
            
            if preferred_cuisine in restaurant_cuisine or restaurant_cuisine in preferred_cuisine:
                score += 25  # Perfect match
            elif self._is_related_cuisine(preferred_cuisine, restaurant_cuisine):
                score += 15  # Related cuisine
        else:
            score += 12.5  # Neutral score when no preference
        
        # Price preference score (20% weight)
        if preferences.get('price_range'):
            preferred_price = preferences['price_range']
            restaurant_price = restaurant.get('price_range', '')
            
            if preferred_price == restaurant_price:
                score += 20  # Perfect match
            elif self._is_acceptable_price_range(preferred_price, restaurant_price):
                score += 10  # Acceptable range
        else:
            score += 10  # Neutral score when no preference
        
        # Capacity score (15% weight) - favor restaurants with good capacity
        capacity = restaurant.get('capacity', 0)
        if capacity >= 100:
            score += 15  # Large capacity
        elif capacity >= 50:
            score += 12  # Medium capacity
        elif capacity >= 20:
            score += 8   # Small capacity
        else:
            score += 5   # Very small capacity
        
        return round(score, 2)
    
    def _is_related_cuisine(self, cuisine1: str, cuisine2: str) -> bool:
        """Check if two cuisines are related."""
        related_cuisines = {
            'italian': ['mediterranean', 'european'],
            'french': ['european', 'mediterranean'],
            'chinese': ['asian', 'japanese', 'thai'],
            'japanese': ['asian', 'chinese', 'thai'],
            'thai': ['asian', 'chinese', 'japanese'],
            'indian': ['asian', 'thai'],
            'mexican': ['american', 'latin'],
            'american': ['mexican', 'latin']
        }
        
        return cuisine2 in related_cuisines.get(cuisine1, [])
    
    def _is_acceptable_price_range(self, preferred: str, restaurant: str) -> bool:
        """Check if restaurant price range is acceptable based on preference."""
        price_levels = {'$': 1, '$$': 2, '$$$': 3, '$$$$': 4}
        
        preferred_level = price_levels.get(preferred, 2)
        restaurant_level = price_levels.get(restaurant, 2)
        
        # Accept within 1 level difference
        return abs(preferred_level - restaurant_level) <= 1
    
    def _get_fallback_recommendations(self, preferences: Dict[str, Any], limit: int, start_time: float) -> Dict[str, Any]:
        """
        Provide fallback recommendations when primary search fails.
        
        Fallback strategies:
        1. Remove strict filters and try broader search
        2. Get highly rated restaurants regardless of preferences
        3. Get random sample if all else fails
        """
        logger.info("Using fallback recommendation strategy")
        
        try:
            # Strategy 1: Broader search with relaxed filters
            query = self.supabase.table('restaurants').select('*')
            
            # Only apply rating filter if specified
            if preferences.get('min_rating'):
                min_rating = max(3.0, float(preferences['min_rating']) - 1.0)  # Relax by 1 star
                query = query.gte('rating', min_rating)
            else:
                query = query.gte('rating', 3.5)  # Default to good restaurants
            
            result = query.order('rating', desc=True).limit(limit).execute()
            
            if result.data:
                response_time = time.time() - start_time
                return {
                    'recommendations': result.data,
                    'fallback_used': True,
                    'total_count': len(result.data),
                    'response_time': response_time,
                    'message': self._generate_fallback_message(preferences)
                }
            
            # Strategy 2: Get any restaurants if nothing found
            result = self.supabase.table('restaurants').select('*').limit(limit).execute()
            
            response_time = time.time() - start_time
            return {
                'recommendations': result.data,
                'fallback_used': True,
                'total_count': len(result.data),
                'response_time': response_time,
                'message': "Here are some popular restaurants you might enjoy"
            }
            
        except Exception as e:
            logger.error(f"Fallback strategy failed: {e}")
            response_time = time.time() - start_time
            return {
                'recommendations': [],
                'fallback_used': True,
                'total_count': 0,
                'response_time': response_time,
                'message': "Unable to load recommendations at this time"
            }
    
    def _generate_message(self, preferences: Dict[str, Any], count: int) -> str:
        """Generate a personalized message based on preferences and results."""
        if count == 0:
            return "No restaurants found matching your criteria"
        
        parts = []
        
        if preferences.get('cuisine'):
            parts.append(f"{preferences['cuisine']} cuisine")
        
        if preferences.get('city'):
            parts.append(f"in {preferences['city']}")
        
        if preferences.get('price_range'):
            parts.append(f"in the {preferences['price_range']} price range")
        
        if preferences.get('min_rating'):
            parts.append(f"with {preferences['min_rating']}+ star rating")
        
        if parts:
            criteria = ", ".join(parts)
            return f"Found {count} excellent restaurants for {criteria}"
        else:
            return f"Here are {count} top-rated restaurants for you"
    
    def _generate_fallback_message(self, preferences: Dict[str, Any]) -> str:
        """Generate message for fallback recommendations."""
        if preferences.get('cuisine'):
            return f"We couldn't find exact matches for {preferences['cuisine']} cuisine, but here are some highly-rated alternatives"
        elif preferences.get('city'):
            return f"Here are some top restaurants, including options near {preferences['city']}"
        else:
            return "Here are some highly-rated restaurants you might enjoy"
    
    def get_cuisine_recommendations(self, cuisine: str, limit: int = 5) -> List[Dict]:
        """Get recommendations for a specific cuisine."""
        preferences = {'cuisine': cuisine, 'min_rating': 4.0}
        result = self.get_recommendations(preferences, limit)
        return result['recommendations']
    
    def get_location_recommendations(self, city: str, limit: int = 5) -> List[Dict]:
        """Get recommendations for a specific location."""
        preferences = {'city': city, 'min_rating': 4.0}
        result = self.get_recommendations(preferences, limit)
        return result['recommendations']
    
    def get_price_range_recommendations(self, price_range: str, limit: int = 5) -> List[Dict]:
        """Get recommendations for a specific price range."""
        preferences = {'price_range': price_range, 'min_rating': 3.5}
        result = self.get_recommendations(preferences, limit)
        return result['recommendations']

# Create singleton instance
recommendation_engine = RecommendationEngine()

# Export for use in other modules
__all__ = ['recommendation_engine', 'RecommendationEngine']
