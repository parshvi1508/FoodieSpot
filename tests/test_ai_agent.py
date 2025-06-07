import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import ai_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent import RestaurantAI

class TestRestaurantAI:
    
    @pytest.fixture
    def mock_together_client(self):
        """Mock Together.ai client"""
        with patch('ai_agent.Together') as mock_together:
            mock_client = MagicMock()
            mock_together.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def mock_requests(self):
        """Mock requests for API calls"""
        with patch('ai_agent.requests') as mock_req:
            yield mock_req
    
    @pytest.fixture
    def ai_agent(self, mock_together_client):
        """Create AI agent instance with mocked dependencies"""
        return RestaurantAI()
    
    def test_initialization(self, ai_agent):
        """Test AI agent initialization"""
        assert ai_agent.client is not None
        assert len(ai_agent.tools) == 2
        assert ai_agent.context == []
        
        # Check tool definitions
        tool_names = [tool['function']['name'] for tool in ai_agent.tools]
        assert 'search_restaurants' in tool_names
        assert 'create_reservation' in tool_names
    
    def test_search_restaurants_tool_call(self, ai_agent, mock_together_client, mock_requests):
        """Test restaurant search via tool call"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': [
                {'name': 'Mario\'s Bistro', 'cuisine': 'Italian'},
                {'name': 'Bella Vista', 'cuisine': 'Italian'},
                {'name': 'Little Italy', 'cuisine': 'Italian'}
            ]
        }
        mock_requests.post.return_value = mock_response
        
        # Mock Together.ai response with tool call
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = 'search_restaurants'
        mock_tool_call.function.arguments = json.dumps({
            'cuisine': 'Italian',
            'location': 'New York',
            'min_rating': 4.0
        })
        mock_tool_call.id = 'tool_123'
        
        # First response with tool call
        mock_message_1 = MagicMock()
        mock_message_1.tool_calls = [mock_tool_call]
        mock_message_1.content = None
        
        # Final response after tool execution
        mock_message_2 = MagicMock()
        mock_message_2.content = "I found 3 great Italian restaurants for you!"
        mock_message_2.tool_calls = None
        
        mock_together_client.chat.completions.create.side_effect = [
            MagicMock(choices=[MagicMock(message=mock_message_1)]),
            MagicMock(choices=[MagicMock(message=mock_message_2)])
        ]
        
        response = ai_agent.chat("Find Italian restaurants in New York with 4+ stars")
        
        assert "great Italian restaurants" in response
        assert len(ai_agent.context) == 4  # user + assistant + tool + final assistant
        mock_requests.post.assert_called_once()
    
    def test_create_reservation_tool_call(self, ai_agent, mock_together_client, mock_requests):
        """Test reservation creation via tool call"""
        # Mock successful reservation API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'success': True,
            'data': {'id': 'RES_12345'}
        }
        mock_requests.post.return_value = mock_response
        
        # Mock tool call
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = 'create_reservation'
        mock_tool_call.function.arguments = json.dumps({
            'restaurant_id': '123',
            'user_name': 'John Doe',
            'user_email': 'john@example.com',
            'party_size': 4,
            'datetime': '2025-06-15T19:00:00'
        })
        mock_tool_call.id = 'tool_456'
        
        # First response with tool call
        mock_message_1 = MagicMock()
        mock_message_1.tool_calls = [mock_tool_call]
        mock_message_1.content = None
        
        # Final response after tool execution
        mock_message_2 = MagicMock()
        mock_message_2.content = "Your reservation has been confirmed!"
        mock_message_2.tool_calls = None
        
        mock_together_client.chat.completions.create.side_effect = [
            MagicMock(choices=[MagicMock(message=mock_message_1)]),
            MagicMock(choices=[MagicMock(message=mock_message_2)])
        ]
        
        response = ai_agent.chat("Book a table for 4 at restaurant 123 tomorrow at 7PM")
        
        assert "confirmed" in response
        assert len(ai_agent.context) == 4  # user + assistant + tool + final assistant
        mock_requests.post.assert_called_once()
    
    def test_direct_conversation_no_tools(self, ai_agent, mock_together_client):
        """Test direct conversation without tool calls"""
        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_message.content = "Hello! I'm here to help you with restaurant reservations."
        
        mock_together_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )
        
        response = ai_agent.chat("Hello, how can you help me?")
        
        assert "help you with restaurant" in response
        assert len(ai_agent.context) == 2  # user + assistant only
    
    def test_api_error_handling(self, ai_agent, mock_requests):
        """Test API error handling"""
        # Mock failed API call
        mock_requests.post.side_effect = Exception("Connection failed")
        
        result = ai_agent._process_tool('search_restaurants', {'cuisine': 'Italian'})
        
        assert result == "No restaurants found"
    
    def test_invalid_tool_call(self, ai_agent):
        """Test handling of invalid tool calls"""
        result = ai_agent._process_tool('invalid_tool', {})
        
        assert result == "Unknown tool"
    
    def test_context_management(self, ai_agent, mock_together_client):
        """Test conversation context accumulation"""
        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_message.content = "Response"
        
        mock_together_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )
        
        # Multiple conversation turns
        ai_agent.chat("First message")
        ai_agent.chat("Second message")
        ai_agent.chat("Third message")
        
        assert len(ai_agent.context) == 6  # 3 user + 3 assistant messages
        assert ai_agent.context[0]['role'] == 'user'
        assert ai_agent.context[1]['role'] == 'assistant'
        assert ai_agent.context[2]['role'] == 'user'
        assert ai_agent.context[3]['role'] == 'assistant'
        assert ai_agent.context[4]['role'] == 'user'
        assert ai_agent.context[5]['role'] == 'assistant'
    
    def test_search_restaurants_api_call(self, ai_agent, mock_requests):
        """Test direct API call for restaurant search"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': [{'name': 'Test Restaurant'}]
        }
        mock_requests.post.return_value = mock_response
        
        result = ai_agent._call_api('restaurants', {'cuisine': 'Italian'})
        
        assert result['success'] is True
        assert len(result['data']) == 1
        mock_requests.post.assert_called_with(
            'http://localhost:5000/api/restaurants',
            json={'cuisine': 'Italian'},
            timeout=10
        )
    
    def test_failed_api_call(self, ai_agent, mock_requests):
        """Test failed API call handling"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests.post.return_value = mock_response
        
        result = ai_agent._call_api('restaurants', {})
        
        assert result is None
    
    def test_tool_parameter_validation(self, ai_agent):
        """Test tool parameter processing"""
        # Valid parameters
        params = {
            'cuisine': 'Japanese',
            'price_range': '$$$',
            'min_rating': 4.5
        }
        
        # This should not raise an exception
        result = ai_agent._process_tool('search_restaurants', params)
        assert isinstance(result, str)
    
    def test_reservation_parameters(self, ai_agent, mock_requests):
        """Test reservation with all parameters"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'data': {'id': 'RES_789'}}
        mock_requests.post.return_value = mock_response
        
        params = {
            'restaurant_id': '456',
            'user_name': 'Jane Smith',
            'user_email': 'jane@example.com',
            'party_size': 2,
            'datetime': '2025-06-20T20:00:00',
            'special_requests': 'Window seat please'
        }
        
        result = ai_agent._process_tool('create_reservation', params)
        
        assert 'RES_789' in result
        mock_requests.post.assert_called_with(
            'http://localhost:5000/api/reservations',
            json=params,
            timeout=10
        )

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
            mock_query.execute.return_value = mock_result
            mock_supabase_client.table.return_value.select.return_value = mock_query
            
            # Force API first mode
            ai_agent_with_supabase.api_available = True
            ai_agent_with_supabase.use_api_first = True
            
            result = ai_agent_with_supabase._call_api('restaurants', {}, method='GET')
            
            assert result['success'] is True
            assert result['source'] == 'supabase'
            assert len(result['data']) == 1

        def test_get_status_with_supabase(self, ai_agent_with_supabase, mock_supabase_client):
            """Test status retrieval with Supabase statistics"""
            # Mock database statistics
            mock_restaurants_count = MagicMock()
            mock_restaurants_count.count = 150
            
            mock_reservations_count = MagicMock()
            mock_reservations_count.count = 75
            
            def mock_table_side_effect(table_name):
                mock_table = MagicMock()
                if table_name == 'restaurants':
                    mock_table.select.return_value.execute.return_value = mock_restaurants_count
                elif table_name == 'reservations':
                    mock_table.select.return_value.execute.return_value = mock_reservations_count
                return mock_table
            
            mock_supabase_client.table.side_effect = mock_table_side_effect
            
            status = ai_agent_with_supabase.get_status()
            
            assert 'database_stats' in status
            assert status['database_stats']['restaurants'] == 150
            assert status['database_stats']['reservations'] == 75
