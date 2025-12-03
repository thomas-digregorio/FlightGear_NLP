"""
NLP Parser Module

Uses a small local LLM to parse natural language commands into structured intents.
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import re


class NLParser:
    """Natural Language Parser using a small local LLM."""
    
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        """
        Initialize the NLP parser with a small LLM.
        
        Args:
            model_name: HuggingFace model name (default: TinyLlama)
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading LLM model: {model_name} on {self.device}...")
        self._load_model()
    
    def _load_model(self):
        """Load the LLM model and tokenizer."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # Set pad token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                low_cpu_mem_usage=True
            )
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            self.model.eval()
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to rule-based parsing...")
            self.model = None
            self.tokenizer = None
    
    def _create_prompt(self, user_input):
        """
        Create a prompt for the LLM to extract command intent.
        
        Args:
            user_input: Natural language command from user
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a flight control assistant. Extract the command intent from the user's natural language input.

Available commands:
- change_speed: Change aircraft speed (requires speed_value in knots)
- change_direction: Change heading/direction (requires heading_deg in degrees 0-360, or direction like "left", "right", "north", etc.)
- change_altitude: Change altitude (requires altitude_ft in feet)
- takeoff: Initiate takeoff sequence
- land: Initiate landing sequence
- status: Get current aircraft status

User input: "{user_input}"

Respond ONLY with a JSON object in this exact format:
{{
    "intent": "command_name",
    "parameters": {{
        "speed_value": number or null,
        "heading_deg": number or null,
        "direction": "string or null",
        "altitude_ft": number or null
    }}
}}

JSON:"""
        return prompt
    
    def _parse_llm_response(self, response_text):
        """
        Parse LLM response to extract JSON command.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Dictionary with intent and parameters, or None if parsing fails
        """
        # Try to extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                command = json.loads(json_str)
                return command
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _rule_based_parse(self, user_input):
        """
        Fallback rule-based parser if LLM is not available.
        
        Args:
            user_input: Natural language command
            
        Returns:
            Dictionary with intent and parameters
        """
        user_input_lower = user_input.lower()
        
        # Check for brake commands
        if any(word in user_input_lower for word in ['release brake', 'brakes off', 'unbrake']):
            return {
                "intent": "release_brakes",
                "parameters": {}
            }
        if any(word in user_input_lower for word in ['parking brake', 'set brake', 'brake on']):
            return {
                "intent": "set_brakes",
                "parameters": {}
            }
        
        # Check for takeoff intent
        if any(word in user_input_lower for word in ['takeoff', 'take off', 'take-off', 'launch', 'depart']):
            return {
                "intent": "takeoff",
                "parameters": {}
            }
        
        # Check for landing intent
        if any(word in user_input_lower for word in ['land', 'landing', 'touchdown']):
            return {
                "intent": "land",
                "parameters": {}
            }
        
        # Check for status intent
        if any(word in user_input_lower for word in ['status', 'speed', 'altitude', 'heading', 'where', 'what']):
            if any(word in user_input_lower for word in ['what', 'show', 'tell', 'status', 'where']):
                return {
                    "intent": "status",
                    "parameters": {}
                }
        
        # Check for altitude change
        altitude_keywords = ['altitude', 'height', 'feet', 'ft', 'climb', 'descend', 'ascend']
        if any(keyword in user_input_lower for keyword in altitude_keywords):
            # Extract number
            numbers = re.findall(r'\d+', user_input)
            altitude_value = int(numbers[0]) if numbers else None
            
            if 'increase' in user_input_lower or 'climb' in user_input_lower or 'ascend' in user_input_lower or 'up' in user_input_lower:
                # Get current altitude and add to it
                return {
                    "intent": "change_altitude",
                    "parameters": {"altitude_ft": altitude_value, "relative": "increase"}
                }
            elif 'decrease' in user_input_lower or 'descend' in user_input_lower or 'down' in user_input_lower:
                # Get current altitude and subtract from it
                return {
                    "intent": "change_altitude",
                    "parameters": {"altitude_ft": altitude_value, "relative": "decrease"}
                }
            elif altitude_value:
                # Absolute altitude
                return {
                    "intent": "change_altitude",
                    "parameters": {"altitude_ft": altitude_value}
                }
        
        # Check for speed change
        speed_keywords = ['speed', 'velocity', 'knots', 'kts']
        if any(keyword in user_input_lower for keyword in speed_keywords):
            # Extract number
            numbers = re.findall(r'\d+', user_input)
            speed_value = int(numbers[0]) if numbers else None
            
            if 'increase' in user_input_lower or 'faster' in user_input_lower or 'accelerate' in user_input_lower:
                return {
                    "intent": "change_speed",
                    "parameters": {"speed_value": speed_value or 250}
                }
            elif 'decrease' in user_input_lower or 'slow' in user_input_lower or 'reduce' in user_input_lower:
                return {
                    "intent": "change_speed",
                    "parameters": {"speed_value": speed_value or 150}
                }
            elif speed_value:
                return {
                    "intent": "change_speed",
                    "parameters": {"speed_value": speed_value}
                }
        
        # Check for direction change
        direction_keywords = ['turn', 'heading', 'direction', 'course', 'bear', 'head']
        if any(keyword in user_input_lower for keyword in direction_keywords):
            # Extract heading number
            numbers = re.findall(r'\d+', user_input)
            heading_deg = int(numbers[0]) if numbers else None
            
            # Check for relative directions
            if 'left' in user_input_lower:
                return {
                    "intent": "change_direction",
                    "parameters": {"direction": "left", "heading_deg": heading_deg}
                }
            elif 'right' in user_input_lower:
                return {
                    "intent": "change_direction",
                    "parameters": {"direction": "right", "heading_deg": heading_deg}
                }
            # Check for cardinal directions
            elif 'north' in user_input_lower:
                return {
                    "intent": "change_direction",
                    "parameters": {"heading_deg": 0}
                }
            elif 'south' in user_input_lower:
                return {
                    "intent": "change_direction",
                    "parameters": {"heading_deg": 180}
                }
            elif 'east' in user_input_lower:
                return {
                    "intent": "change_direction",
                    "parameters": {"heading_deg": 90}
                }
            elif 'west' in user_input_lower:
                return {
                    "intent": "change_direction",
                    "parameters": {"heading_deg": 270}
                }
            elif heading_deg:
                return {
                    "intent": "change_direction",
                    "parameters": {"heading_deg": heading_deg}
                }
        
        # Default: status query
        return {
            "intent": "status",
            "parameters": {}
        }
    
    def parse_command(self, user_input):
        """
        Parse natural language command into structured intent.
        
        Args:
            user_input: Natural language command string
            
        Returns:
            Dictionary with 'intent' and 'parameters' keys
        """
        if not user_input or not user_input.strip():
            return {
                "intent": "status",
                "parameters": {}
            }
        
        # Use LLM if available
        if self.model and self.tokenizer:
            try:
                prompt = self._create_prompt(user_input)
                
                # Tokenize with attention mask
                inputs = self.tokenizer(
                    prompt, 
                    return_tensors="pt",
                    padding=True,
                    truncation=True
                ).to(self.device)
                
                # Generate
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs.input_ids,
                        attention_mask=inputs.attention_mask,
                        max_new_tokens=150,
                        temperature=0.3,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                
                # Decode response
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Extract the generated part (after the prompt)
                if prompt in response:
                    response = response.split(prompt)[-1].strip()
                
                # Parse JSON from response
                command = self._parse_llm_response(response)
                if command and command.get("intent"):
                    return command
                
            except Exception as e:
                print(f"LLM parsing error: {e}, falling back to rule-based parser")
        
        # Fallback to rule-based parsing
        return self._rule_based_parse(user_input)

