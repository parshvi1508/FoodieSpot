# AI conversation logic
# src/ai/agent.py
import os
from together import Together

class ReservationAgent:
    def __init__(self):
        self.client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
    
    def generate_response(self, prompt):
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct-Turbo",
            messages=[{"role": "user", "content": prompt}],
            tools=[{
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": "Check restaurant availability",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "restaurant_id": {"type": "string"},
                            "time": {"type": "string"}
                        }
                    }
                }
            }]
        )
        return response.choices[0].message.content
