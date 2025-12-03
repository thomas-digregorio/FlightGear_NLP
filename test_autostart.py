"""
Test script to find the correct autostart property path
"""

from flightgear_controller_simple import FlightGearController
import time

fg = FlightGearController(http_port=8080)
fg.connect()

print("Testing autostart property paths...")
print("=" * 60)

# List of possible autostart property paths
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
]

print("\nChecking which autostart properties exist...")
for path in autostart_paths:
    value = fg.get_property(path)
    if value is not None:
        print(f"✓ Found: {path} = {value}")

print("\n" + "=" * 60)
print("Attempting to trigger autostart...")
print("(Check FlightGear window - engine should start)")

# Try to trigger autostart by setting each property to 1
for path in autostart_paths:
    print(f"\nTrying: {path}")
    try:
        # Try setting to 1
        fg.set_property(path, 1)
        time.sleep(1.0)
        
        # Check if engine started
        engine_running = fg.get_property('/engines/engine/running')
        if engine_running and engine_running > 0:
            print(f"✓ SUCCESS! Engine started using: {path}")
            break
        else:
            # Try setting to 0 then 1 (toggle)
            fg.set_property(path, 0)
            time.sleep(0.2)
            fg.set_property(path, 1)
            time.sleep(1.0)
            engine_running = fg.get_property('/engines/engine/running')
            if engine_running and engine_running > 0:
                print(f"✓ SUCCESS! Engine started using toggle on: {path}")
                break
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("Final check:")
engine_running = fg.get_property('/engines/engine/running')
print(f"Engine running: {engine_running}")

fg.disconnect()

