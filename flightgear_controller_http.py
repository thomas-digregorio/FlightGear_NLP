"""
FlightGear Controller Module (HTTP-based)

Handles communication with FlightGear via HTTP interface.
This is more reliable than telnet.
"""

import requests
import time
import re


class FlightGearController:
    """Controller for interacting with FlightGear via HTTP."""
    
    def __init__(self, host='localhost', http_port=8080, timeout=5):
        """
        Initialize FlightGear controller.
        
        Args:
            host: FlightGear host (default: localhost)
            http_port: HTTP port (default: 8080)
            timeout: Request timeout in seconds
        """
        self.host = host
        self.http_port = http_port
        self.timeout = timeout
        self.base_url = f"http://{host}:{http_port}"
        self.connected = False
    
    def connect(self):
        """Establish connection to FlightGear."""
        try:
            # Test connection by trying to access the HTTP interface
            response = requests.get(f"{self.base_url}/", timeout=self.timeout)
            if response.status_code == 200:
                self.connected = True
                print(f"Connected to FlightGear HTTP interface at {self.host}:{self.http_port}")
                return True
            else:
                print(f"FlightGear HTTP interface returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"Failed to connect to FlightGear HTTP interface at {self.base_url}")
            print("Make sure FlightGear is running with: fgfs --httpd=8080")
            self.connected = False
            return False
        except Exception as e:
            print(f"Failed to connect to FlightGear: {e}")
            print("Make sure FlightGear is running with: fgfs --httpd=8080")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close connection to FlightGear."""
        self.connected = False
        print("Disconnected from FlightGear")
    
    def get_property(self, property_path, debug=False):
        """
        Get a property value from FlightGear via HTTP.
        
        Args:
            property_path: Path to property (e.g., '/sim/position/latitude')
            debug: If True, print debugging information
            
        Returns:
            Property value as float or None if error
        """
        if not self.connected:
            return None
        
        try:
            # FlightGear HTTP interface uses JSON API
            # Try different URL formats
            formats = [
                f"{self.base_url}/json/property/get?path={property_path}",
                f"{self.base_url}/json/property{property_path}",
                f"{self.base_url}{property_path}",
            ]
            
            for url in formats:
                try:
                    response = requests.get(url, timeout=self.timeout)
                    if response.status_code == 200:
                        # Try to parse as JSON first
                        try:
                            data = response.json()
                            # If it's a dict, look for 'value' key
                            if isinstance(data, dict):
                                value_str = str(data.get('value', data.get('data', '')))
                            else:
                                value_str = str(data)
                        except:
                            # If not JSON, treat as text
                            value_str = response.text.strip()
                        
                        try:
                            value = float(value_str)
                            if debug:
                                print(f"DEBUG - {property_path} = {value} (format: {url})")
                            return value
                        except ValueError:
                            continue
                    elif debug and response.status_code != 404:
                        print(f"DEBUG - HTTP {response.status_code} for {url}")
                except:
                    continue
            
            if debug:
                print(f"DEBUG - All formats failed for {property_path}")
            return None
        except Exception as e:
            if debug:
                print(f"DEBUG - Exception getting {property_path}: {e}")
            return None
    
    def set_property(self, property_path, value):
        """
        Set a property value in FlightGear via HTTP.
        
        Args:
            property_path: Path to property
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            # FlightGear HTTP interface uses JSON API
            # Try different URL formats
            formats = [
                (f"{self.base_url}/json/property/set?path={property_path}&value={value}", 'GET'),
                (f"{self.base_url}/json/property/set", 'POST'),
                (f"{self.base_url}{property_path}", 'PUT'),
            ]
            
            for url, method in formats:
                try:
                    if method == 'GET':
                        response = requests.get(url, timeout=self.timeout)
                    elif method == 'POST':
                        response = requests.post(url, json={'path': property_path, 'value': value}, timeout=self.timeout)
                    else:  # PUT
                        response = requests.put(url, data=str(value), timeout=self.timeout)
                    
                    if response.status_code == 200:
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            return False
    
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
        """Set throttle value (0.0 to 1.0)."""
        value = max(0.0, min(1.0, float(value)))
        return self.set_property('/controls/engines/engine/throttle', value)
    
    def set_aileron(self, value):
        """Set aileron value (-1.0 to 1.0)."""
        value = max(-1.0, min(1.0, float(value)))
        return self.set_property('/controls/flight/aileron', value)
    
    def set_elevator(self, value):
        """Set elevator value (-1.0 to 1.0)."""
        value = max(-1.0, min(1.0, float(value)))
        return self.set_property('/controls/flight/elevator', value)
    
    def set_rudder(self, value):
        """Set rudder value (-1.0 to 1.0)."""
        value = max(-1.0, min(1.0, float(value)))
        return self.set_property('/controls/flight/rudder', value)
    
    def set_heading(self, heading_deg):
        """Set target heading by adjusting controls."""
        current_state = self.get_aircraft_state()
        current_heading = current_state.get('heading_deg', 0)
        
        diff = heading_deg - current_heading
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        
        aileron_value = max(-1.0, min(1.0, diff / 30.0))
        return self.set_aileron(aileron_value)
    
    def set_speed(self, target_speed_kts):
        """Set target speed by adjusting throttle."""
        current_state = self.get_aircraft_state()
        current_speed = current_state.get('speed_kts', 0)
        
        speed_diff = target_speed_kts - current_speed
        throttle_adjustment = speed_diff / 100.0
        
        current_throttle = current_state.get('throttle', 0.5)
        new_throttle = max(0.0, min(1.0, current_throttle + throttle_adjustment))
        
        return self.set_throttle(new_throttle)
    
    def initiate_takeoff(self):
        """Initiate takeoff sequence."""
        self.set_throttle(1.0)
        self.set_elevator(0.3)
        self.set_aileron(0.0)
        self.set_rudder(0.0)
        return True
    
    def initiate_landing(self):
        """Initiate landing sequence."""
        self.set_throttle(0.3)
        self.set_elevator(-0.2)
        return True
    
    def test_connection(self):
        """Test the connection."""
        print("\nTesting FlightGear HTTP connection...")
        test_prop = '/sim/time/elapsed-sec'
        value = self.get_property(test_prop, debug=True)
        print(f"Test property value: {value}")
        
        print("\nTrying to get throttle property...")
        throttle = self.get_property('/controls/engines/engine/throttle', debug=True)
        print(f"Throttle value: {throttle}")
        
        return throttle is not None

