from typing import Dict, Optional, Union
import os
from abc import ABC, abstractmethod
import json
from openai import AsyncOpenAI

class LLMProcessor(ABC):
    @abstractmethod
    async def process_input(self, user_input: str) -> Dict[str, Union[str, int]]:
        """Process natural language input and return structured ticket data."""
        pass

    @staticmethod
    def _create_prompt(user_input: str) -> str:
        """Create a prompt for the LLM to extract ticket information."""
        return f"""You are Terry, a witty AI Product Manager. Create a ticket in JSON format with these fields:

{{
    "title": "Technical title summarizing the task",
    "description": "Full ticket description with your usual wit and style",
    "priority": "P0/P1/P2/P3",
    "impact_area": "Core Product/User Experience/Technical Debt/Infrastructure",
    "scores": {{
        "revenue_potential": 0-100,
        "user_impact": 0-100,
        "technical_complexity": 0-100,
        "strategic_alignment": 0-100
    }}
}}

User request: {user_input}

Respond with valid JSON only.
"""

    def _normalize_response(self, response_data: Dict) -> Dict[str, Union[str, int]]:
        """Normalize the response to match the expected format."""
        # Extract scores from nested structure if needed
        scores = response_data.get('scores', {})
        if isinstance(scores, dict):
            return {
                'title': response_data.get('title', 'Untitled'),
                'description': response_data.get('description', ''),
                'revenue_potential': scores.get('revenue_potential', 50),
                'user_impact': scores.get('user_impact', 50),
                'technical_complexity': scores.get('technical_complexity', 50),
                'strategic_alignment': scores.get('strategic_alignment', 50)
            }
        else:
            # Handle flat structure if scores aren't nested
            return {
                'title': response_data.get('title', 'Untitled'),
                'description': response_data.get('description', ''),
                'revenue_potential': response_data.get('revenue_potential', 50),
                'user_impact': response_data.get('user_impact', 50),
                'technical_complexity': response_data.get('technical_complexity', 50),
                'strategic_alignment': response_data.get('strategic_alignment', 50)
            }

class OpenAIProcessor(LLMProcessor):
    def __init__(self, api_key: Optional[str] = None):
        try:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key not found")
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

    async def process_input(self, user_input: str) -> Dict[str, Union[str, int]]:
        """Process input using OpenAI to extract ticket information."""
        prompt = self._create_prompt(user_input)
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert software development project manager who excels at analyzing and structuring development tickets. Your responses must always be valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={ "type": "json_object" }
            )
            
            response_text = response.choices[0].message.content
            response_data = json.loads(response_text)
            return self._normalize_response(response_data)
            
        except Exception as e:
            raise ValueError(f"Failed to process OpenAI response: {str(e)}")

class LlamaProcessor(LLMProcessor):
    def __init__(self, model_path: str):
        try:
            from llama_cpp import Llama
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,  # Increased context window
                n_threads=4  # Parallel processing
            )
        except ImportError:
            raise ImportError("llama-cpp-python not installed. Run: pip install llama-cpp-python")

    async def process_input(self, user_input: str) -> Dict[str, Union[str, int]]:
        """Process input using local Llama model to extract ticket information."""
        prompt = self._create_prompt(user_input)
        
        # Add explicit JSON instruction for Llama
        prompt += "\nProvide your response as a valid JSON object and nothing else:"
        
        try:
            response = self.llm(
                prompt,
                max_tokens=1000,
                temperature=0.7,
                stop=["}"],  # Stop at the end of JSON
                echo=False
            )
            
            # Clean up response text to ensure valid JSON
            response_text = response["choices"][0]["text"].strip()
            if not response_text.endswith("}"):
                response_text += "}"
            response_text = self._format_llama_response(response_text)
            
            response_data = json.loads(response_text)
            return self._normalize_response(response_data)
            
        except Exception as e:
            raise ValueError(f"Failed to process Llama response: {str(e)}")

    def _format_llama_response(self, text: str) -> str:
        """Clean up Llama response to ensure valid JSON."""
        # Find the first '{' and last '}'
        start = text.find('{')
        end = text.rfind('}')
        
        if start == -1 or end == -1:
            raise ValueError("No valid JSON object found in response")
            
        # Extract the JSON part
        json_text = text[start:end+1]
        
        # Remove any trailing commas before closing braces
        json_text = json_text.replace(',}', '}')
        json_text = json_text.replace(',\n}', '}')
        
        return json_text