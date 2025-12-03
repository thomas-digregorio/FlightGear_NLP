"""
Command Executor Module

Maps LLM intents to FlightGear control commands and executes them.
"""

from flightgear_controller_simple import FlightGearController


class CommandExecutor:
    """Executes parsed commands on FlightGear."""
    
    def __init__(self, flightgear_controller):
        """
        Initialize command executor.
        
        Args:
            flightgear_controller: FlightGearController instance
        """
        self.fg = flightgear_controller
    
    def execute(self, parsed_command):
        """
        Execute a parsed command.
        
        Args:
            parsed_command: Dictionary with 'intent' and 'parameters' keys
            
        Returns:
            Dictionary with 'success', 'message', and optional 'data' keys
        """
        if not self.fg.connected:
            return {
                "success": False,
                "message": "Not connected to FlightGear. Please connect first."
            }
        
        intent = parsed_command.get("intent", "").lower()
        parameters = parsed_command.get("parameters", {})
        
        try:
            if intent == "change_speed":
                return self._execute_change_speed(parameters)
            elif intent == "change_direction":
                return self._execute_change_direction(parameters)
            elif intent == "change_altitude":
                return self._execute_change_altitude(parameters)
            elif intent == "takeoff" or intent == "take_off":
                return self._execute_takeoff()
            elif intent == "release_brakes":
                return self._execute_release_brakes()
            elif intent == "set_brakes":
                return self._execute_set_brakes()
            elif intent == "land":
                return self._execute_land()
            elif intent == "status":
                return self._execute_status()
            else:
                return {
                    "success": False,
                    "message": f"Unknown command intent: {intent}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing command: {str(e)}"
            }
    
    def _execute_change_speed(self, parameters):
        """
        Execute speed change command.
        
        Args:
            parameters: Dictionary with 'speed_value' key
            
        Returns:
            Execution result dictionary
        """
        speed_value = parameters.get("speed_value")
        
        if speed_value is None:
            # Get current speed and adjust based on context
            state = self.fg.get_aircraft_state()
            current_speed = state.get('speed_kts', 200)
            # Default: increase by 50 knots
            speed_value = current_speed + 50
        
        # Validate speed (reasonable range: 50-500 knots)
        speed_value = max(50, min(500, float(speed_value)))
        
        success = self.fg.set_speed(speed_value)
        
        if success:
            return {
                "success": True,
                "message": f"Setting target speed to {speed_value:.0f} knots",
                "data": {"target_speed_kts": speed_value}
            }
        else:
            return {
                "success": False,
                "message": "Failed to set speed"
            }
    
    def _execute_change_direction(self, parameters):
        """
        Execute direction change command.
        
        Args:
            parameters: Dictionary with 'heading_deg' or 'direction' key
            
        Returns:
            Execution result dictionary
        """
        heading_deg = parameters.get("heading_deg")
        direction = parameters.get("direction", "").lower()
        
        # Get current heading
        state = self.fg.get_aircraft_state()
        current_heading = state.get('heading_deg', 0)
        
        # Calculate target heading
        if heading_deg is not None:
            target_heading = float(heading_deg)
        elif direction == "left":
            # Turn left by specified degrees or default 30
            turn_degrees = parameters.get("heading_deg", 30)
            target_heading = (current_heading - turn_degrees) % 360
        elif direction == "right":
            # Turn right by specified degrees or default 30
            turn_degrees = parameters.get("heading_deg", 30)
            target_heading = (current_heading + turn_degrees) % 360
        else:
            # Default: maintain current heading
            target_heading = current_heading
        
        # Normalize heading to 0-360
        target_heading = target_heading % 360
        
        success = self.fg.set_heading(target_heading)
        
        if success:
            return {
                "success": True,
                "message": f"Changing heading to {target_heading:.0f} degrees",
                "data": {"target_heading_deg": target_heading}
            }
        else:
            return {
                "success": False,
                "message": "Failed to change heading"
            }
    
    def _execute_change_altitude(self, parameters):
        """
        Execute altitude change command.
        
        Args:
            parameters: Dictionary with 'altitude_ft' key, optionally 'relative' key
            
        Returns:
            Execution result dictionary
        """
        altitude_ft = parameters.get("altitude_ft")
        relative = parameters.get("relative", "").lower()
        
        # Get current altitude
        state = self.fg.get_aircraft_state()
        current_altitude = state.get('altitude_ft', 0)
        
        # Calculate target altitude
        if altitude_ft is None:
            # No specific altitude given, use relative change
            if relative == "increase" or relative == "climb":
                # Increase by default 1000 feet
                target_altitude = (current_altitude or 5000) + 1000
            elif relative == "decrease" or relative == "descend":
                # Decrease by default 1000 feet
                target_altitude = max(1000, (current_altitude or 5000) - 1000)
            else:
                # Default: increase by 1000 feet
                target_altitude = (current_altitude or 5000) + 1000
        else:
            # Specific altitude given
            if relative == "increase" or relative == "climb":
                # Add to current altitude
                target_altitude = (current_altitude or 0) + float(altitude_ft)
            elif relative == "decrease" or relative == "descend":
                # Subtract from current altitude
                target_altitude = max(1000, (current_altitude or 0) - float(altitude_ft))
            else:
                # Absolute altitude
                target_altitude = float(altitude_ft)
        
        # Validate altitude (reasonable range: 1000-50000 feet)
        target_altitude = max(1000, min(50000, target_altitude))
        
        success = self.fg.set_altitude(target_altitude)
        
        if success:
            return {
                "success": True,
                "message": f"Changing altitude to {target_altitude:.0f} feet",
                "data": {"target_altitude_ft": target_altitude}
            }
        else:
            return {
                "success": False,
                "message": "Failed to change altitude"
            }
    
    def _execute_takeoff(self):
        """
        Execute takeoff command.
        
        Returns:
            Execution result dictionary
        """
        print("Starting engine... (this may take a few seconds)")
        success = self.fg.initiate_takeoff()
        
        if success:
            # Check if engine is actually running
            import time
            time.sleep(2)  # Give engine time to start
            engine_running = self.fg.get_property('/engines/engine/running')
            
            if engine_running and engine_running > 0:
                return {
                    "success": True,
                    "message": "✓ Takeoff sequence complete! Engine running, brakes released, full throttle engaged!",
                    "data": {}
                }
            else:
                return {
                    "success": True,
                    "message": "⚠ Takeoff sequence initiated, but engine may still be starting. Try 'increase speed' in a few seconds.",
                    "data": {}
                }
        else:
            return {
                "success": False,
                "message": "Failed to initiate takeoff"
            }
    
    def _execute_release_brakes(self):
        """Execute release brakes command."""
        success = self.fg.set_property('/controls/gear/brake-parking', 0)
        if success:
            return {
                "success": True,
                "message": "Parking brake released!",
                "data": {}
            }
        else:
            return {
                "success": False,
                "message": "Failed to release brakes"
            }
    
    def _execute_set_brakes(self):
        """Execute set parking brake command."""
        success = self.fg.set_property('/controls/gear/brake-parking', 1)
        if success:
            return {
                "success": True,
                "message": "Parking brake set!",
                "data": {}
            }
        else:
            return {
                "success": False,
                "message": "Failed to set brakes"
            }
    
    def _execute_land(self):
        """
        Execute landing command.
        
        Returns:
            Execution result dictionary
        """
        success = self.fg.initiate_landing()
        
        if success:
            return {
                "success": True,
                "message": "Initiating landing sequence...",
                "data": {}
            }
        else:
            return {
                "success": False,
                "message": "Failed to initiate landing"
            }
    
    def _execute_status(self):
        """
        Execute status query command.
        
        Returns:
            Execution result dictionary with aircraft state
        """
        state = self.fg.get_aircraft_state()
        
        # Helper function to safely format values
        def safe_format(value, default=0, format_str=".2f"):
            if value is None:
                value = default
            try:
                return format(value, format_str)
            except (ValueError, TypeError):
                return str(default)
        
        # Format status message with safe formatting
        lat = safe_format(state.get('latitude'), 0, ".4f")
        lon = safe_format(state.get('longitude'), 0, ".4f")
        alt = safe_format(state.get('altitude_ft'), 0, ".0f")
        speed = safe_format(state.get('speed_kts'), 0, ".0f")
        gspeed = safe_format(state.get('ground_speed_kts'), 0, ".0f")
        heading = safe_format(state.get('heading_deg'), 0, ".1f")
        pitch = safe_format(state.get('pitch_deg'), 0, ".1f")
        roll = safe_format(state.get('roll_deg'), 0, ".1f")
        throttle = safe_format(state.get('throttle'), 0, ".2f")
        aileron = safe_format(state.get('aileron'), 0, ".2f")
        
        status_msg = f"""Current Aircraft Status:
  Position: Lat {lat}°, Lon {lon}°
  Altitude: {alt} ft
  Speed: {speed} knots (ground: {gspeed} kts)
  Heading: {heading}°
  Pitch: {pitch}°, Roll: {roll}°
  Controls: Throttle {throttle}, Aileron {aileron}"""
        
        return {
            "success": True,
            "message": status_msg,
            "data": state
        }

