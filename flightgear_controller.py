"""
FlightGear Controller Module

Handles communication with FlightGear via telnet interface.
Provides methods to read aircraft state and send control commands.
"""

import telnetlib
import time
import re


class FlightGearController:
    """Controller for interacting with FlightGear via telnet."""
    
    def __init__(self, host='localhost', port=5500, timeout=5):
        """
        Initialize FlightGear controller.
        
        Args:
            host: FlightGear host (default: localhost)
            port: Telnet port (default: 5500)
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.tn = None
        self.connected = False
    
    def connect(self):
        """Establish connection to FlightGear."""
        try:
            self.tn = telnetlib.Telnet(self.host, self.port, self.timeout)
            
            # FlightGear telnet might need a moment to initialize
            time.sleep(0.2)
            
            # Try to read any initial greeting
            try:
                # Read any available data (greeting, etc.)
                initial_data = self.tn.read_very_eager()
                if initial_data:
                    print(f"FlightGear greeting: {initial_data.decode('ascii', errors='ignore')[:100]}")
            except:
                pass
            
            # Try sending a test command to verify the connection works
            # Some FlightGear versions need this to "wake up" the telnet interface
            try:
                self.tn.write(b"data\n")
                time.sleep(0.1)
                # Try to read response
                try:
                    test_response = self.tn.read_until(b"\n", timeout=0.5)
                    print(f"Test command response: {test_response.decode('ascii', errors='ignore')[:100]}")
                except:
                    # No response is okay, some versions don't respond to 'data'
                    pass
            except:
                pass
            
            self.connected = True
            print(f"Connected to FlightGear at {self.host}:{self.port}")
            print("⚠ If commands don't work, FlightGear may not have been started with --telnet=5500")
            return True
        except Exception as e:
            print(f"Failed to connect to FlightGear: {e}")
            print("Make sure FlightGear is running with: fgfs --telnet=5500")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close connection to FlightGear."""
        if self.tn:
            self.tn.close()
            self.connected = False
            print("Disconnected from FlightGear")
    
    def _send_command(self, command, debug=False):
        """
        Send a command to FlightGear and return response.
        
        Args:
            command: Command string to send
            debug: If True, print the response for debugging
            
        Returns:
            Response string from FlightGear
        """
        if not self.connected:
            raise ConnectionError("Not connected to FlightGear")
        
        try:
            # Clear any pending data
            try:
                self.tn.read_very_eager()
            except:
                pass
            
            # Send command with newline
            cmd_bytes = f"{command}\n".encode('ascii')
            self.tn.write(cmd_bytes)
            
            # FlightGear may need a moment to process
            time.sleep(0.05)
            
            # Read response - FlightGear typically echoes the command and adds the result
            # Try multiple read strategies
            response = ""
            try:
                # Try reading until newline
                data = self.tn.read_until(b"\n", timeout=1)
                response = data.decode('ascii', errors='ignore').strip()
            except:
                # If that fails, try reading available data
                try:
                    data = self.tn.read_very_eager()
                    if data:
                        response = data.decode('ascii', errors='ignore').strip()
                except:
                    pass
            
            if debug:
                print(f"DEBUG - Command: '{command}'")
                print(f"DEBUG - Raw response bytes: {data if 'data' in locals() else 'None'}")
                print(f"DEBUG - Decoded response: '{response}'")
            
            return response
        except ConnectionError:
            raise
        except Exception as e:
            if debug:
                print(f"Error sending command '{command}': {e}")
            return ""
    
    def get_property(self, property_path, debug=False):
        """
        Get a property value from FlightGear.
        
        Args:
            property_path: Path to property (e.g., '/sim/position/latitude')
            debug: If True, print debugging information
            
        Returns:
            Property value as float or None if error
        """
        try:
            response = self._send_command(f"get {property_path}", debug=debug)
            if not response:
                if debug:
                    print(f"DEBUG - No response for {property_path}")
                return None
            # Parse response: "get /path/to/property = value"
            # FlightGear format: "get /path/to/property = value" or just "value"
            match = re.search(r'=\s*([-\d.Ee]+)', response)
            if match:
                try:
                    value = float(match.group(1))
                    if debug:
                        print(f"DEBUG - {property_path} = {value}")
                    return value
                except ValueError:
                    if debug:
                        print(f"DEBUG - Could not convert '{match.group(1)}' to float")
                    return None
            # Try to find number directly if no "=" found
            match = re.search(r'([-\d.Ee]+)', response)
            if match:
                try:
                    value = float(match.group(1))
                    if debug:
                        print(f"DEBUG - {property_path} = {value} (no = sign)")
                    return value
                except ValueError:
                    return None
            if debug:
                print(f"DEBUG - Could not parse response: '{response}'")
            return None
        except Exception as e:
            if debug:
                print(f"DEBUG - Exception getting {property_path}: {e}")
            return None
    
    def test_connection(self):
        """
        Test the connection by trying to get a simple property.
        
        Returns:
            True if connection works, False otherwise
        """
        print("\nTesting FlightGear connection...")
        # Try a simple property that should always exist
        test_prop = '/sim/time/elapsed-sec'
        response = self._send_command(f"get {test_prop}", debug=True)
        print(f"Test response: '{response}'")
        
        # Also try to list properties
        print("\nTrying to get throttle property...")
        throttle = self.get_property('/controls/engines/engine/throttle', debug=True)
        print(f"Throttle value: {throttle}")
        
        return throttle is not None
    
    def set_property(self, property_path, value):
        """
        Set a property value in FlightGear.
        
        Args:
            property_path: Path to property
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        response = self._send_command(f"set {property_path} {value}")
        # Check if command was successful
        return "=" in response or "set" in response.lower()
    
    def get_aircraft_state(self):
        """
        Get current aircraft state.
        
        Returns:
            Dictionary with aircraft state information
        """
        state = {}
        
        # Position
        state['latitude'] = self.get_property('/sim/position/latitude-deg')
        state['longitude'] = self.get_property('/sim/position/longitude-deg')
        state['altitude_ft'] = self.get_property('/sim/position/altitude-ft')
        
        # Speed
        state['speed_kts'] = self.get_property('/velocities/airspeed-kt')
        state['ground_speed_kts'] = self.get_property('/velocities/groundspeed-kt')
        
        # Orientation
        state['heading_deg'] = self.get_property('/orientation/heading-deg')
        state['pitch_deg'] = self.get_property('/orientation/pitch-deg')
        state['roll_deg'] = self.get_property('/orientation/roll-deg')
        
        # Controls
        state['throttle'] = self.get_property('/controls/engines/engine/throttle')
        state['aileron'] = self.get_property('/controls/flight/aileron')
        state['elevator'] = self.get_property('/controls/flight/elevator')
        state['rudder'] = self.get_property('/controls/flight/rudder')
        
        return state
    
    def set_throttle(self, value):
        """
        Set throttle value (0.0 to 1.0).
        
        Args:
            value: Throttle value between 0.0 and 1.0
        """
        value = max(0.0, min(1.0, float(value)))
        return self.set_property('/controls/engines/engine/throttle', value)
    
    def set_aileron(self, value):
        """
        Set aileron value (-1.0 to 1.0, negative = left, positive = right).
        
        Args:
            value: Aileron value between -1.0 and 1.0
        """
        value = max(-1.0, min(1.0, float(value)))
        return self.set_property('/controls/flight/aileron', value)
    
    def set_elevator(self, value):
        """
        Set elevator value (-1.0 to 1.0, negative = down, positive = up).
        
        Args:
            value: Elevator value between -1.0 and 1.0
        """
        value = max(-1.0, min(1.0, float(value)))
        return self.set_property('/controls/flight/elevator', value)
    
    def set_rudder(self, value):
        """
        Set rudder value (-1.0 to 1.0, negative = left, positive = right).
        
        Args:
            value: Rudder value between -1.0 and 1.0
        """
        value = max(-1.0, min(1.0, float(value)))
        return self.set_property('/controls/flight/rudder', value)
    
    def set_heading(self, heading_deg):
        """
        Set target heading by adjusting controls.
        This is a simplified implementation that adjusts rudder/aileron.
        
        Args:
            heading_deg: Target heading in degrees (0-360)
        """
        current_state = self.get_aircraft_state()
        current_heading = current_state.get('heading_deg', 0)
        
        # Calculate heading difference
        diff = heading_deg - current_heading
        # Normalize to -180 to 180
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        
        # Adjust aileron based on heading difference (simplified)
        # Positive diff means turn right, negative means turn left
        aileron_value = max(-1.0, min(1.0, diff / 30.0))  # Scale factor
        return self.set_aileron(aileron_value)
    
    def set_speed(self, target_speed_kts):
        """
        Set target speed by adjusting throttle.
        
        Args:
            target_speed_kts: Target speed in knots
        """
        current_state = self.get_aircraft_state()
        current_speed = current_state.get('speed_kts', 0)
        
        # Simple proportional control
        speed_diff = target_speed_kts - current_speed
        throttle_adjustment = speed_diff / 100.0  # Scale factor
        
        current_throttle = current_state.get('throttle', 0.5)
        new_throttle = max(0.0, min(1.0, current_throttle + throttle_adjustment))
        
        return self.set_throttle(new_throttle)
    
    def initiate_takeoff(self):
        """
        Initiate takeoff sequence by setting throttle and adjusting controls.
        
        Returns:
            True if successful
        """
        # Set full throttle for takeoff
        self.set_throttle(1.0)
        # Slight nose up for takeoff
        self.set_elevator(0.3)
        # Center aileron and rudder
        self.set_aileron(0.0)
        self.set_rudder(0.0)
        return True
    
    def initiate_landing(self):
        """
        Initiate landing sequence by reducing throttle and adjusting for descent.
        
        Returns:
            True if successful
        """
        # Reduce throttle
        self.set_throttle(0.3)
        # Slight nose down
        self.set_elevator(-0.2)
        return True

