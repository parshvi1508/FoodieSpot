import os
import json
import requests
from together import Together
from dotenv import load_dotenv

load_dotenv()

class RestaurantAI:
    def __init__(self):
        self.client = Together(api_key=os.getenv('TOGETHER_API_KEY', 'test_key'))
        self.context = []
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_restaurants",
                    "description": "Search restaurants by filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cuisine": {"type": "string"},
                            "location": {"type": "string"},
                            "price_range": {"type": "string", "enum": ["$", "$$", "$$$", "$$$$"]},
                            "min_rating": {"type": "number", "minimum": 1, "maximum": 5}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_reservation",
                    "description": "Create restaurant reservation",
                    "parameters": {
                        "type": "object",
                        "required": ["restaurant_id", "user_name", "user_email", "party_size", "datetime"],
                        "properties": {
                            "restaurant_id": {"type": "string"},
                            "user_name": {"type": "string"},
                            "user_email": {"type": "string", "format": "email"},
                            "party_size": {"type": "integer", "minimum": 1},
                            "datetime": {"type": "string", "format": "date-time"},
                            "special_requests": {"type": "string"}
                        }
                    }
                }
            }
        ]

    def _call_api(self, endpoint: str, params: dict):
        """Call Flask API endpoints"""
        try:
            response = requests.post(
                f"http://localhost:5000/api/{endpoint}",
                json=params,
                timeout=10
            )
            return response.json() if response.status_code in [200, 201] else None
        except Exception as e:
            print(f"API Error: {str(e)}")
            return None

    def _process_tool(self, tool_name: str, parameters: dict) -> str:
        """Execute tool calls"""
        if tool_name == "search_restaurants":
            results = self._call_api("restaurants", parameters)
            if results and 'data' in results:
                restaurant_names = [r['name'] for r in results['data'][:3]]
                return f"Found {len(results['data'])} restaurants: {', '.join(restaurant_names)}"
            return "No restaurants found"
        
        if tool_name == "create_reservation":
            result = self._call_api("reservations", parameters)
            if result and 'data' in result:
                return f"Reservation confirmed: {result['data']['id']}"
            elif result and 'id' in result:
                return f"Reservation confirmed: {result['id']}"
            return "Reservation failed"
        
        return "Unknown tool"

    def chat(self, user_input: str) -> str:
        """Process chat with AI agent"""
        # Add user message to context
        user_message = {"role": "user", "content": user_input}
        self.context.append(user_message)
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                messages=self.context,
                tools=self.tools,
                temperature=0.7
            )
            
            msg = response.choices[0].message
            
            # Add assistant message to context
            assistant_message = {
                "role": "assistant", 
                "content": msg.content,
                "tool_calls": msg.tool_calls if hasattr(msg, 'tool_calls') else None
            }
            self.context.append(assistant_message)
            
            # Process tool calls if any
            if msg.tool_calls:
                for tool in msg.tool_calls:
                    result = self._process_tool(
                        tool.function.name,
                        json.loads(tool.function.arguments)
                    )
                    # Add tool result to context
                    tool_message = {
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool.id
                    }
                    self.context.append(tool_message)
                
                # Get final response with tool results
                final_response = self.client.chat.completions.create(
                    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                    messages=self.context,
                    temperature=0.7
                )
                
                final_msg = final_response.choices[0].message
                final_assistant_message = {
                    "role": "assistant",
                    "content": final_msg.content
                }
                self.context.append(final_assistant_message)
                
                return final_msg.content
            
            return msg.content
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.context.append({"role": "assistant", "content": error_msg})
            return error_msg

# Initialize singleton agent
ai_agent = RestaurantAI()
