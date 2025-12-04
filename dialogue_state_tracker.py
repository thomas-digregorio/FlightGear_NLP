"""
Dialogue State Tracker Module

Maintains conversation context, user goals, and progress across multiple turns.
Handles slot filling, coreference resolution, and state updates.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class DialogueStateTracker:
    """
    Tracks dialogue state across multiple conversation turns.
    
    Maintains:
    - Current intent and slots
    - Conversation history
    - Pending confirmations
    - Entity references for coreference resolution
    """
    
    def __init__(self):
        """Initialize an empty dialogue state."""
        self.current_intent: Optional[str] = None
        self.slots: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.pending_slots: List[str] = []  # Slots that need to be filled
        self.entity_references: Dict[str, Any] = {}  # For coreference resolution
        self.last_action: Optional[str] = None
        self.turn_count: int = 0
        
    def update_state(self, parsed_command: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """
        Update dialogue state based on new parsed command and user input.
        
        Args:
            parsed_command: Dictionary with 'intent' and 'parameters' keys
            user_input: Raw user input for context
            
        Returns:
            Updated dialogue state dictionary
        """
        self.turn_count += 1
        
        # Store conversation history
        self.conversation_history.append({
            'turn': self.turn_count,
            'user_input': user_input,
            'intent': parsed_command.get('intent'),
            'parameters': parsed_command.get('parameters', {}).copy(),
            'timestamp': datetime.now().isoformat()
        })
        
        intent = parsed_command.get('intent', '').lower()
        parameters = parsed_command.get('parameters', {})
        
        # Handle corrections/updates
        if self.is_correction(user_input):
            # User is correcting previous command
            # If parser got wrong intent (e.g., status), use previous intent
            if not intent or intent == 'status':
                if self.current_intent:
                    intent = self.current_intent.lower()
                    parsed_command['intent'] = self.current_intent
            
            self._handle_correction(intent, parameters, user_input)
            # After handling correction, get the updated intent
            if self.current_intent:
                intent = self.current_intent.lower()
        else:
            # Normal state update
            self._update_intent_and_slots(intent, parameters)
        
        # Extract entities for coreference resolution
        self._extract_entities(user_input, intent, parameters)
        
        # Resolve coreferences in current input
        resolved_parameters = self._resolve_coreferences(user_input, parameters)
        
        # Update slots with resolved parameters
        for key, value in resolved_parameters.items():
            if value is not None:
                self.slots[key] = value
        
        # Update current intent (use corrected intent if available)
        if intent:
            self.current_intent = intent
        
        # Determine pending slots
        self._update_pending_slots()
        
        return self.get_state()
    
    def is_correction(self, user_input: str) -> bool:
        """
        Detect if user input is a correction or update to previous command.
        
        Args:
            user_input: User's natural language input
            
        Returns:
            True if this appears to be a correction
        """
        correction_keywords = [
            'actually', 'correction', 'change', 'update', 'make it', 
            'instead', 'rather', 'no wait', 'scratch that', 'never mind',
            'cancel', 'abort', 'wrong', 'not that'
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in correction_keywords)
    
    def _handle_correction(self, intent: str, parameters: Dict[str, Any], user_input: str):
        """
        Handle corrections to previous commands.
        
        Args:
            intent: New intent (may be None if just updating parameters)
            parameters: New parameters
            user_input: User input for context
        """
        # Look for explicit parameter updates in the text FIRST
        # This helps when the parser didn't extract the intent/parameters correctly
        self._extract_parameter_updates(user_input)
        
        # If intent is provided, update it
        if intent:
            self.current_intent = intent
        # If no intent provided but we have a current intent, keep it
        # (corrections often don't repeat the intent)
        
        # Update only the slots that are mentioned in the correction
        for key, value in parameters.items():
            if value is not None:
                self.slots[key] = value
    
    def _extract_parameter_updates(self, user_input: str):
        """Extract parameter updates from correction text."""
        user_lower = user_input.lower()
        numbers = re.findall(r'\d+', user_input)
        
        if not numbers:
            return
        
        number_value = int(numbers[0])
        
        # Extract altitude updates
        if 'altitude' in user_lower or 'height' in user_lower or 'feet' in user_lower or 'ft' in user_lower:
            self.slots['altitude_ft'] = number_value
        # Extract speed updates
        elif 'speed' in user_lower or 'knots' in user_lower or 'kts' in user_lower:
            self.slots['speed_value'] = number_value
        # Extract heading updates
        elif 'heading' in user_lower or 'direction' in user_lower or 'turn' in user_lower or 'degrees' in user_lower:
            self.slots['heading_deg'] = number_value
        # If no specific keyword but we have a previous intent, infer from context
        elif self.current_intent:
            if self.current_intent == 'change_altitude':
                self.slots['altitude_ft'] = number_value
            elif self.current_intent == 'change_speed':
                self.slots['speed_value'] = number_value
            elif self.current_intent == 'change_direction':
                self.slots['heading_deg'] = number_value
    
    def _update_intent_and_slots(self, intent: str, parameters: Dict[str, Any]):
        """
        Update intent and slots with new information.
        
        Args:
            intent: Current intent
            parameters: Parameters from parsed command
        """
        if intent:
            self.current_intent = intent
        
        # Merge new parameters into slots (don't overwrite with None)
        for key, value in parameters.items():
            if value is not None:
                self.slots[key] = value
    
    def _extract_entities(self, user_input: str, intent: str, parameters: Dict[str, Any]):
        """
        Extract entities from user input for coreference resolution.
        
        Args:
            user_input: User's natural language input
            intent: Current intent
            parameters: Extracted parameters
        """
        # Store aircraft-related entities
        if 'aircraft' in user_input.lower() or 'plane' in user_input.lower():
            self.entity_references['aircraft'] = {
                'type': 'aircraft',
                'mentioned_in_turn': self.turn_count
            }
        
        # Store waypoint/point references
        waypoint_pattern = r'(?:waypoint|point|location)\s+(\w+)'
        waypoint_match = re.search(waypoint_pattern, user_input, re.IGNORECASE)
        if waypoint_match:
            waypoint_name = waypoint_match.group(1)
            self.entity_references[waypoint_name] = {
                'type': 'waypoint',
                'name': waypoint_name,
                'mentioned_in_turn': self.turn_count
            }
        
        # Store parameter values as entities
        if parameters.get('altitude_ft'):
            self.entity_references['last_altitude'] = parameters['altitude_ft']
        if parameters.get('speed_value'):
            self.entity_references['last_speed'] = parameters['speed_value']
        if parameters.get('heading_deg'):
            self.entity_references['last_heading'] = parameters['heading_deg']
    
    def _resolve_coreferences(self, user_input: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve coreferences (pronouns, references) in user input.
        
        Args:
            user_input: User's natural language input
            parameters: Extracted parameters
            
        Returns:
            Parameters with coreferences resolved
        """
        resolved = parameters.copy()
        user_lower = user_input.lower()
        
        # Resolve "it" - usually refers to aircraft or last mentioned entity
        if ' it ' in user_lower or user_lower.startswith('it ') or user_lower.endswith(' it'):
            # "it" likely refers to the aircraft
            # If we have a pending intent, apply "it" to that intent
            if self.current_intent and not any(v is not None for v in parameters.values()):
                # User might be saying "do it" or "execute it"
                # Use previous slots if available
                for key in ['altitude_ft', 'speed_value', 'heading_deg']:
                    if key in self.slots and resolved.get(key) is None:
                        resolved[key] = self.slots[key]
        
        # Resolve "there" - refers to last mentioned location
        if ' there' in user_lower or user_lower.startswith('there'):
            # "there" might refer to last waypoint or location
            if 'last_waypoint' in self.entity_references:
                # Could set a waypoint parameter if we had one
                pass
        
        # Resolve "the first one", "the second one" - refers to entities in history
        ordinal_pattern = r'(?:the\s+)?(first|second|third|last)\s+one'
        ordinal_match = re.search(ordinal_pattern, user_input, re.IGNORECASE)
        if ordinal_match:
            ordinal = ordinal_match.group(1).lower()
            # Look for entities in conversation history
            if ordinal == 'first' and len(self.conversation_history) > 0:
                first_turn = self.conversation_history[0]
                first_params = first_turn.get('parameters', {})
                # Use parameters from first turn
                for key, value in first_params.items():
                    if value is not None and resolved.get(key) is None:
                        resolved[key] = value
        
        # Resolve "that" - refers to last mentioned parameter
        if ' that' in user_lower:
            # Use last mentioned values
            if 'last_altitude' in self.entity_references and resolved.get('altitude_ft') is None:
                resolved['altitude_ft'] = self.entity_references['last_altitude']
            if 'last_speed' in self.entity_references and resolved.get('speed_value') is None:
                resolved['speed_value'] = self.entity_references['last_speed']
            if 'last_heading' in self.entity_references and resolved.get('heading_deg') is None:
                resolved['heading_deg'] = self.entity_references['last_heading']
        
        return resolved
    
    def _update_pending_slots(self):
        """Update list of slots that still need to be filled."""
        self.pending_slots = []
        
        if not self.current_intent:
            return
        
        # Define required slots for each intent
        required_slots = {
            'change_speed': ['speed_value'],
            'change_altitude': ['altitude_ft'],
            'change_direction': ['heading_deg', 'direction'],
        }
        
        required = required_slots.get(self.current_intent, [])
        for slot in required:
            if slot not in self.slots or self.slots[slot] is None:
                self.pending_slots.append(slot)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current dialogue state.
        
        Returns:
            Dictionary containing current dialogue state
        """
        return {
            'current_intent': self.current_intent,
            'slots': self.slots.copy(),
            'pending_slots': self.pending_slots.copy(),
            'turn_count': self.turn_count,
            'last_action': self.last_action,
            'has_context': len(self.conversation_history) > 0
        }
    
    def get_context_for_parser(self) -> str:
        """
        Get conversation context as a string for the NLP parser.
        
        Returns:
            Formatted context string
        """
        if not self.conversation_history:
            return ""
        
        context_parts = []
        
        # Add recent conversation history (last 3 turns)
        recent_history = self.conversation_history[-3:]
        for turn in recent_history:
            context_parts.append(
                f"Turn {turn['turn']}: User said '{turn['user_input']}' "
                f"→ Intent: {turn['intent']}, Parameters: {turn['parameters']}"
            )
        
        # Add current state
        if self.current_intent:
            context_parts.append(f"Current intent: {self.current_intent}")
        if self.slots:
            context_parts.append(f"Filled slots: {self.slots}")
        if self.pending_slots:
            context_parts.append(f"Pending slots: {self.pending_slots}")
        
        return "\n".join(context_parts)
    
    def merge_parsed_with_state(self, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge newly parsed command with existing dialogue state.
        
        This fills in missing parameters from state and handles partial commands.
        
        Args:
            parsed_command: Newly parsed command from NLP parser
            
        Returns:
            Merged command with state information
        """
        merged = parsed_command.copy()
        intent = merged.get('intent', '').lower()
        parameters = merged.get('parameters', {})
        
        # Special handling for corrections: if parser returned status but we detect a correction,
        # use the previous intent
        original_input = merged.get('_original_input', '')
        is_correction = self.is_correction(original_input) if original_input else False
        if is_correction and (not intent or intent == 'status') and self.current_intent:
            merged['intent'] = self.current_intent
            intent = self.current_intent.lower()
        
        # If no intent in new command but we have one in state, use state intent
        if not intent and self.current_intent:
            merged['intent'] = self.current_intent
            intent = self.current_intent.lower()
        
        # Fill missing parameters from state (but don't overwrite new values)
        for key, value in self.slots.items():
            if parameters.get(key) is None and value is not None:
                parameters[key] = value
        
        merged['parameters'] = parameters
        
        return merged
    
    def reset_state(self):
        """Reset dialogue state (useful for starting new conversation)."""
        self.current_intent = None
        self.slots = {}
        self.conversation_history = []
        self.pending_slots = []
        self.entity_references = {}
        self.last_action = None
        self.turn_count = 0
    
    def set_last_action(self, action: str):
        """Record the last action taken by the system."""
        self.last_action = action

