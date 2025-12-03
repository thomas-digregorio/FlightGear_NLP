"""
FlightGear Controller Module (using flightgear-python library)

Simple and reliable controller using the flightgear-python library.
"""

from flightgear_python.fg_if import HTTPConnection
import time


class FlightGearController:
    """Controller for interacting with FlightGear via HTTP using flightgear-python."""
    
    def __init__(self, host='localhost', http_port=8080, timeout=5):
        """
        Initialize FlightGear controller.
        
        Args:
            host: FlightGear host (default: localhost)
            http_port: HTTP port (default: 8080)
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.http_port = http_port
        self.timeout = timeout
        self.conn = None
        self.connected = False
    
    def connect(self):
        """Establish connection to FlightGear."""
        try:
            self.conn = HTTPConnection(self.host, self.http_port)
            self.connected = True
            print(f"Connected to FlightGear HTTP interface at {self.host}:{self.http_port}")
            return True
        except Exception as e:
            print(f"Failed to connect to FlightGear: {e}")
            print("Make sure FlightGear is running with: fgfs --httpd=8080")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close connection to FlightGear."""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        self.connected = False
        print("Disconnected from FlightGear")
    
    def get_property(self, property_path, debug=False):
        """
        Get a property value from FlightGear.
        
        Args:
            property_path: Path to property (e.g., '/sim/position/latitude')
            debug: If True, print debugging information
            
        Returns:
            Property value as float or None if error
        """
        if not self.connected or not self.conn:
            return None
        
        try:
            value = self.conn.get_prop(property_path)
            if debug:
                print(f"DEBUG - {property_path} = {value}")
            return float(value) if value is not None else None
        except Exception as e:
            if debug:
                print(f"DEBUG - Exception getting {property_path}: {e}")
            return None
    
    def set_property(self, property_path, value):
        """
        Set a property value in FlightGear.
        
        Args:
            property_path: Path to property
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected or not self.conn:
            return False
        
        try:
            self.conn.set_prop(property_path, value)
            return True
        except Exception as e:
            return False
    
    def _get_property_with_fallback(self, property_paths):
        """Try multiple property paths and return the first valid value."""
        for path in property_paths:
            value = self.get_property(path)
            if value is not None:
                return value
        return None
    
    def get_aircraft_state(self):
        """Get current aircraft state."""
        state = {}
        
        # Position - try multiple property paths
        state['latitude'] = self._get_property_with_fallback([
            '/position/latitude-deg',
            '/sim/position/latitude-deg',
            '/position/latitude',
        ])
        state['longitude'] = self._get_property_with_fallback([
            '/position/longitude-deg',
            '/sim/position/longitude-deg',
            '/position/longitude',
        ])
        state['altitude_ft'] = self._get_property_with_fallback([
            '/position/altitude-ft',
            '/sim/position/altitude-ft',
            '/position/altitude',
            '/position/altitude-agl-ft',
        ])
        
        # Speed
        state['speed_kts'] = self._get_property_with_fallback([
            '/velocities/airspeed-kt',
            '/velocities/airspeed-kts',
            '/velocities/uBody-fps',  # Body velocity, may need conversion
        ])
        state['ground_speed_kts'] = self._get_property_with_fallback([
            '/velocities/groundspeed-kt',
            '/velocities/groundspeed-kts',
        ])
        
        # Orientation
        state['heading_deg'] = self._get_property_with_fallback([
            '/orientation/heading-deg',
            '/orientation/heading',
        ])
        state['pitch_deg'] = self._get_property_with_fallback([
            '/orientation/pitch-deg',
            '/orientation/pitch',
        ])
        state['roll_deg'] = self._get_property_with_fallback([
            '/orientation/roll-deg',
            '/orientation/roll',
        ])
        
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
    
    def set_altitude(self, target_altitude_ft):
        """
        Set target altitude by adjusting elevator and throttle.
        
        Args:
            target_altitude_ft: Target altitude in feet
            
        Returns:
            True if successful, False otherwise
        """
        current_state = self.get_aircraft_state()
        current_altitude = current_state.get('altitude_ft', 0)
        
        if current_altitude is None:
            # If we can't read current altitude, use a simple climb/descend approach
            # Assume we want to climb if target is high
            if target_altitude_ft > 10000:
                # Climb: nose up and increase throttle
                self.set_elevator(0.3)
                self.set_throttle(0.8)
            else:
                # Descend: nose down and reduce throttle
                self.set_elevator(-0.2)
                self.set_throttle(0.4)
            return True
        
        altitude_diff = target_altitude_ft - current_altitude
        
        # Adjust elevator based on altitude difference
        if altitude_diff > 500:
            # Need to climb significantly
            elevator_value = 0.3  # Nose up
            throttle_value = 0.8  # Increase power
        elif altitude_diff > 100:
            # Small climb
            elevator_value = 0.15
            throttle_value = 0.7
        elif altitude_diff < -500:
            # Need to descend significantly
            elevator_value = -0.3  # Nose down
            throttle_value = 0.3  # Reduce power
        elif altitude_diff < -100:
            # Small descent
            elevator_value = -0.15
            throttle_value = 0.5
        else:
            # Close to target, level off
            elevator_value = 0.0
            throttle_value = 0.6
        
        self.set_elevator(elevator_value)
        self.set_throttle(throttle_value)
        
        return True
    
    def start_engine(self):
        """Start the aircraft engine using FlightGear's autostart function."""
        # Release parking brake first
        self.set_property('/controls/gear/brake-parking', 0)
        
        # Try to trigger FlightGear's autostart function
        # This is the easiest and most reliable method
        autostart_paths = [
            '/sim/autostart',
            '/sim/aircraft/autostart',
            '/sim/command/autostart',
            '/sim/aircraft/c172p/autostart',
            '/sim/aircraft/c172p/autostart-request',
            '/sim/aircraft/c172p/autostart/request',
            '/sim/aircraft/c172p/autostart/trigger',
            '/sim/aircraft/c172p/autostart/do-autostart',
            '/sim/aircraft/c172p/autostart/enabled',
            '/sim/aircraft/c172p/autostart/active',
            '/sim/aircraft/c172p/autostart/execute',
            '/sim/aircraft/c172p/autostart/run',
        ]
        
        # Try each autostart path
        for path in autostart_paths:
            try:
                # Try setting to 1 to trigger autostart
                result = self.set_property(path, 1)
                if result:
                    time.sleep(0.5)
                    # Check if it worked
                    engine_running = self.get_property('/engines/engine/running')
                    if engine_running and engine_running > 0:
                        return True
                    
                    # Try toggle method (set to 0 then 1)
                    self.set_property(path, 0)
                    time.sleep(0.2)
                    self.set_property(path, 1)
                    time.sleep(1.0)
                    engine_running = self.get_property('/engines/engine/running')
                    if engine_running and engine_running > 0:
                        return True
            except:
                continue
        
        # If autostart didn't work, try manual sequence
        # 1. Set magnetos to both
        self.set_property('/controls/engines/engine/magnetos', 3)
        time.sleep(0.2)
        
        # 2. Set mixture to full rich
        self.set_property('/controls/engines/engine/mixture', 1.0)
        time.sleep(0.2)
        
        # 3. Set throttle to idle (needed for starting)
        self.set_throttle(0.1)
        time.sleep(0.2)
        
        # 4. Engage starter
        self.set_property('/controls/engines/engine/starter', 1)
        time.sleep(3.0)  # Wait for engine to start
        
        # 5. Check if engine started
        engine_running = self.get_property('/engines/engine/running')
        
        # 6. Release starter
        self.set_property('/controls/engines/engine/starter', 0)
        
        return engine_running and engine_running > 0
    
    def initiate_takeoff(self):
        """Initiate takeoff sequence."""
        # Release all brakes
        self.set_property('/controls/gear/brake-parking', 0)
        self.set_property('/controls/gear/brake-left', 0)
        self.set_property('/controls/gear/brake-right', 0)
        
        # Start engine using autostart
        print("Starting engine via autostart...")
        engine_started = self.start_engine()
        
        if engine_started:
            print("✓ Engine started successfully!")
        else:
            print("⚠ Engine start may have failed, but continuing...")
        
        # Wait a moment for engine to stabilize
        time.sleep(1.0)
        
        # Set full throttle
        self.set_throttle(1.0)
        
        # Nose up for takeoff
        self.set_elevator(0.3)
        
        # Center controls
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

