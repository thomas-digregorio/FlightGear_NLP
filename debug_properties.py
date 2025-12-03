"""
Debug script to check FlightGear properties
"""

from flightgear_controller_simple import FlightGearController

fg = FlightGearController(http_port=8080)
fg.connect()

# Check various brake and engine properties
properties_to_check = [
    '/controls/gear/brake-parking',
    '/controls/gear/brake-left',
    '/controls/gear/brake-right',
    '/controls/engines/engine/starter',
    '/engines/engine/running',
    '/sim/flight-model/engine/engine-running',
    '/sim/model/engine/engine-running',
    '/controls/engines/engine/mixture',
    '/controls/engines/engine/magnetos',
]

print("Checking FlightGear properties:")
print("=" * 60)

for prop in properties_to_check:
    value = fg.get_property(prop, debug=False)
    print(f"{prop:50} = {value}")

print("\n" + "=" * 60)
print("Current state:")
state = fg.get_aircraft_state()
for key, value in state.items():
    print(f"{key:20} = {value}")

fg.disconnect()

