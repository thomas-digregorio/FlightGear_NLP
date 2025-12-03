"""
Main Entry Point

Chat interface for controlling FlightGear aircraft via natural language.
"""

import sys
import time
from flightgear_controller_simple import FlightGearController
from nlp_parser import NLParser
from command_executor import CommandExecutor


def print_welcome():
    """Print welcome message."""
    print("=" * 60)
    print("FlightGear NLP Control System")
    print("=" * 60)
    print("\nWelcome! You can control the aircraft using natural language.")
    print("Watch the FlightGear window to see your plane react in real-time!")
    print("\nExample commands:")
    print("  - 'take off'")
    print("  - 'increase speed to 250 knots'")
    print("  - 'turn left 30 degrees'")
    print("  - 'head north'")
    print("  - 'land the plane'")
    print("  - 'what's my current speed?'")
    print("\nType 'help' for more commands, 'quit' or 'exit' to stop.")
    print("=" * 60)
    print()


def print_help():
    """Print help message."""
    print("\nAvailable Commands:")
    print("  Speed Control:")
    print("    - 'increase speed to 250 knots'")
    print("    - 'slow down'")
    print("    - 'set speed to 200'")
    print("  Altitude Control:")
    print("    - 'increase altitude to 10000 feet'")
    print("    - 'climb to 15000'")
    print("    - 'descend to 5000'")
    print("    - 'increase altitude by 2000'")
    print("  Direction Control:")
    print("    - 'turn left 30 degrees'")
    print("    - 'turn right'")
    print("    - 'head north' / 'head south' / 'head east' / 'head west'")
    print("    - 'change heading to 090'")
    print("  Takeoff:")
    print("    - 'take off'")
    print("    - 'takeoff'")
    print("    - 'launch'")
    print("  Brakes:")
    print("    - 'release brakes'")
    print("    - 'set parking brake'")
    print("  Landing:")
    print("    - 'land the plane'")
    print("    - 'initiate landing sequence'")
    print("  Status:")
    print("    - 'what's my speed?'")
    print("    - 'show status'")
    print("    - 'where am I?'")
    print("  System:")
    print("    - 'help' - Show this help message")
    print("    - 'watch' or 'monitor' - Show real-time status in terminal")
    print("    - 'quit' or 'exit' - Exit the program")
    print()


def main():
    """Main application loop."""
    print_welcome()
    
    # Initialize components
    print("Initializing components...")
    
    # FlightGear controller
    print("Using flightgear-python library (HTTP interface)")
    fg_controller = FlightGearController(http_port=8080)
    
    # Connect to FlightGear
    print("\nConnecting to FlightGear...")
    if not fg_controller.connect():
        print("\nERROR: Could not connect to FlightGear.")
        print("Please make sure FlightGear is running with:")
        print("  fgfs --httpd=8080")
        print("\nOr use: start_flightgear.bat")
        sys.exit(1)
    
    # Test connection by trying to read a property
    print("Testing connection...")
    if not fg_controller.test_connection():
        print("\n⚠ WARNING: Connected but cannot read properties.")
        print("This usually means:")
        print("  1. FlightGear was NOT started with --httpd=8080")
        print("  2. Port 8080 is blocked by firewall")
        print("\nSOLUTION: Restart FlightGear with: fgfs --httpd=8080")
        print("Or use: start_flightgear.bat")
        print("\nYou can still try commands, but they may not work.")
    
    # NLP parser
    print("Loading NLP parser...")
    nlp_parser = NLParser()
    
    # Command executor
    executor = CommandExecutor(fg_controller)
    
    print("\nSystem ready!")
    print("Note: You'll see the plane react in real-time in the FlightGear window!")
    print("\nYou can now give commands.\n")
    
    # Main command loop
    try:
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nShutting down...")
                    break
                
                if user_input.lower() == 'help':
                    print_help()
                    continue
                
                if user_input.lower() == 'test':
                    print("\nTesting FlightGear connection...")
                    print("Trying to set throttle to 0.8...")
                    result = fg_controller.set_throttle(0.8)
                    print(f"Set throttle result: {result}")
                    time.sleep(0.5)
                    throttle = fg_controller.get_property('/controls/engines/engine/throttle', debug=True)
                    print(f"Current throttle: {throttle}")
                    print("Check the FlightGear window - the throttle should be at 80%")
                    print("If you see the throttle move, the connection is working!\n")
                    continue
                
                if user_input.lower() in ['watch', 'monitor', 'live']:
                    print("\nStarting real-time status monitor (Ctrl+C to stop)...")
                    try:
                        while True:
                            state = fg_controller.get_aircraft_state()
                            # Clear screen (works on most terminals)
                            print("\033[2J\033[H", end="")  # ANSI escape codes
                            print("=" * 60)
                            print("REAL-TIME AIRCRAFT STATUS (Press Ctrl+C to return)")
                            print("=" * 60)
                            print(f"Position:  Lat {state.get('latitude', 0):.4f}°, Lon {state.get('longitude', 0):.4f}°")
                            print(f"Altitude:  {state.get('altitude_ft', 0):.0f} ft")
                            print(f"Speed:     {state.get('speed_kts', 0):.0f} knots (ground: {state.get('ground_speed_kts', 0):.0f} kts)")
                            print(f"Heading:   {state.get('heading_deg', 0):.1f}°")
                            print(f"Pitch:     {state.get('pitch_deg', 0):.1f}°")
                            print(f"Roll:      {state.get('roll_deg', 0):.1f}°")
                            print(f"Throttle:  {state.get('throttle', 0):.2f}")
                            print("=" * 60)
                            time.sleep(0.5)  # Update twice per second
                    except KeyboardInterrupt:
                        print("\n\nReturning to command mode...\n")
                    continue
                
                # Parse command using NLP
                print("Processing command...")
                parsed_command = nlp_parser.parse_command(user_input)
                
                # Debug: show parsed command
                if '--debug' in sys.argv:
                    print(f"DEBUG - Parsed command: {parsed_command}")
                
                # Execute command
                try:
                    result = executor.execute(parsed_command)
                    
                    # Display result
                    if result.get("success"):
                        print(f"\n✓ {result.get('message', 'Command executed successfully')}")
                    else:
                        print(f"\n✗ {result.get('message', 'Command failed')}")
                except ConnectionError as e:
                    print(f"\n✗ Connection error: {e}")
                    print("FlightGear connection lost. Please restart FlightGear and reconnect.")
                    break
                
                # Show quick status after command
                if result.get("success"):
                    state = fg_controller.get_aircraft_state()
                    print(f"   [Alt: {state.get('altitude_ft', 0):.0f}ft | Speed: {state.get('speed_kts', 0):.0f}kts | Heading: {state.get('heading_deg', 0):.0f}°]")
                
                print()  # Blank line for readability
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Shutting down...")
                break
            except Exception as e:
                print(f"\n✗ Error: {e}")
                print("Please try again or type 'help' for assistance.\n")
    
    finally:
        # Cleanup
        print("Cleaning up...")
        fg_controller.disconnect()
        print("Goodbye!")


if __name__ == "__main__":
    main()

