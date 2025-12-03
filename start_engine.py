"""
Script to manually start the engine and test different property paths
"""

from flightgear_controller_simple import FlightGearController
import time

fg = FlightGearController(http_port=8080)
fg.connect()

print("Attempting to start engine...")
print("=" * 60)

# Try different engine start sequences
print("\n1. Setting magnetos to both (3)...")
fg.set_property('/controls/engines/engine/magnetos', 3)
time.sleep(0.2)
print(f"   Magnetos: {fg.get_property('/controls/engines/engine/magnetos')}")

print("\n2. Setting mixture to full (1.0)...")
fg.set_property('/controls/engines/engine/mixture', 1.0)
time.sleep(0.2)
print(f"   Mixture: {fg.get_property('/controls/engines/engine/mixture')}")

print("\n3. Setting throttle to idle (0.1)...")
fg.set_throttle(0.1)
time.sleep(0.2)
print(f"   Throttle: {fg.get_property('/controls/engines/engine/throttle')}")

print("\n4. Engaging starter...")
fg.set_property('/controls/engines/engine/starter', 1)
print("   Starter engaged, waiting 3 seconds...")
time.sleep(3)

print("\n5. Checking if engine is running...")
engine_running = fg.get_property('/engines/engine/running')
print(f"   Engine running: {engine_running}")

if engine_running and engine_running > 0:
    print("\n✓ Engine started successfully!")
    print("6. Releasing starter...")
    fg.set_property('/controls/engines/engine/starter', 0)
    print("7. Setting full throttle...")
    fg.set_throttle(1.0)
else:
    print("\n✗ Engine did not start. Trying alternative methods...")
    
    # Try alternative property paths
    alt_paths = [
        '/sim/model/engine/engine-running',
        '/sim/flight-model/engine/engine-running',
        '/engines/engine[0]/running',
    ]
    
    for path in alt_paths:
        value = fg.get_property(path)
        print(f"   {path} = {value}")
    
    # Try setting engine running directly (if possible)
    print("\nTrying to set engine running directly...")
    fg.set_property('/engines/engine/running', 1)
    time.sleep(0.5)
    engine_running = fg.get_property('/engines/engine/running')
    print(f"   Engine running after direct set: {engine_running}")

print("\n" + "=" * 60)
print("Final state:")
state = fg.get_aircraft_state()
print(f"  Engine running: {fg.get_property('/engines/engine/running')}")
print(f"  Throttle: {state.get('throttle')}")
print(f"  Speed: {state.get('speed_kts')} knots")

fg.disconnect()

