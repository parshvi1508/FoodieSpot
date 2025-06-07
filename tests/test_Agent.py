# Add this to your ai_agent.py for testing
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_connection(self):
    """Test API connection"""
    try:
        result = self._call_api("health", {}, method="GET")
        logger.info(f"Health check result: {result}")
        return result
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return None
    
test_api_connection()