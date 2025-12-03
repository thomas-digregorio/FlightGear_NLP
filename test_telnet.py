"""
Quick test script to verify FlightGear telnet connection manually.
Run this to test if FlightGear telnet is working.
"""

import telnetlib
import time

def test_flightgear_telnet():
    """Test FlightGear telnet connection manually."""
    print("Testing FlightGear telnet connection...")
    print("Make sure FlightGear is running with: fgfs --telnet=5500\n")
    
    try:
        # Connect
        print("Connecting to localhost:5500...")
        tn = telnetlib.Telnet('localhost', 5500, timeout=5)
        print("✓ Connected!")
        
        # Wait a moment
        time.sleep(0.5)
        
        # Read any initial data
        print("\nReading initial data...")
        try:
            initial = tn.read_very_eager()
            if initial:
                print(f"Initial data: {initial}")
            else:
                print("No initial data received")
        except:
            print("Could not read initial data")
        
        # Try sending a simple command
        print("\nSending test command: 'get /sim/time/elapsed-sec'")
        tn.write(b"get /sim/time/elapsed-sec\n")
        time.sleep(1.0)  # Give more time
        
        # Also try without newline first (some versions are picky)
        print("Trying command with carriage return...")
        tn.write(b"get /sim/time/elapsed-sec\r\n")
        time.sleep(1.0)
        
        # Try to read response
        print("Reading response...")
        try:
            response = tn.read_until(b"\n", timeout=2)
            print(f"Response: {response}")
            if response:
                print("✓ SUCCESS! Telnet is working!")
            else:
                print("✗ No response received")
        except Exception as e:
            print(f"✗ Error reading response: {e}")
            print("\nTrying alternative read method...")
            try:
                response = tn.read_very_eager()
                print(f"Response (eager): {response}")
            except Exception as e2:
                print(f"Error: {e2}")
        
        # Try setting a property
        print("\n\nTrying to SET a property: throttle to 0.5")
        tn.write(b"set /controls/engines/engine/throttle 0.5\n")
        time.sleep(0.5)
        
        try:
            set_response = tn.read_until(b"\n", timeout=2)
            print(f"Set response: {set_response}")
        except:
            set_response = tn.read_very_eager()
            print(f"Set response (eager): {set_response}")
        
        tn.close()
        print("\n" + "="*60)
        print("Test complete!")
        print("="*60)
        print("\nIf you saw responses above, telnet is working.")
        print("If all responses were empty, FlightGear telnet server is not enabled.")
        print("\nMake sure FlightGear was started with: fgfs --telnet=5500")
        
    except ConnectionRefusedError:
        print("✗ Connection refused!")
        print("FlightGear is not running or telnet server is not enabled.")
        print("Start FlightGear with: fgfs --telnet=5500")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_flightgear_telnet()

