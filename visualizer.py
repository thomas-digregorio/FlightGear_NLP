"""
Visualization Module

Provides real-time visualization of aircraft state and flight path.
"""

import matplotlib
matplotlib.use('TkAgg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
from collections import deque
import time


class FlightVisualizer:
    """Real-time flight path and state visualizer."""
    
    def __init__(self, max_points=1000):
        """
        Initialize visualizer.
        
        Args:
            max_points: Maximum number of points to store in flight path
        """
        self.max_points = max_points
        self.latitude_history = deque(maxlen=max_points)
        self.longitude_history = deque(maxlen=max_points)
        self.altitude_history = deque(maxlen=max_points)
        self.speed_history = deque(maxlen=max_points)
        self.time_history = deque(maxlen=max_points)
        
        self.start_time = time.time()
        self.fig = None
        self.axes = None
        self.animation = None
        self.running = False
    
    def add_data_point(self, state):
        """
        Add a data point to the history.
        
        Args:
            state: Dictionary with aircraft state
        """
        current_time = time.time() - self.start_time
        
        self.latitude_history.append(state.get('latitude', 0))
        self.longitude_history.append(state.get('longitude', 0))
        self.altitude_history.append(state.get('altitude_ft', 0))
        self.speed_history.append(state.get('speed_kts', 0))
        self.time_history.append(current_time)
    
    def _update_plot(self, frame, flightgear_controller):
        """
        Update the plot with latest data.
        
        Args:
            frame: Animation frame number
            flightgear_controller: FlightGearController instance
        """
        if not flightgear_controller.connected:
            return
        
        # Get current state
        state = flightgear_controller.get_aircraft_state()
        self.add_data_point(state)
        
        if len(self.latitude_history) < 2:
            return
        
        # Clear axes
        for ax in self.axes:
            ax.clear()
        
        # Plot 1: Flight path (latitude vs longitude)
        self.axes[0].plot(
            list(self.longitude_history),
            list(self.latitude_history),
            'b-', linewidth=1.5, alpha=0.7, label='Flight Path'
        )
        if len(self.longitude_history) > 0:
            # Current position marker
            self.axes[0].plot(
                self.longitude_history[-1],
                self.latitude_history[-1],
                'ro', markersize=10, label='Current Position'
            )
        self.axes[0].set_xlabel('Longitude (°)')
        self.axes[0].set_ylabel('Latitude (°)')
        self.axes[0].set_title('Flight Path')
        self.axes[0].grid(True, alpha=0.3)
        self.axes[0].legend()
        
        # Plot 2: Altitude over time
        if len(self.time_history) > 0:
            self.axes[1].plot(
                list(self.time_history),
                list(self.altitude_history),
                'g-', linewidth=1.5
            )
        self.axes[1].set_xlabel('Time (s)')
        self.axes[1].set_ylabel('Altitude (ft)')
        self.axes[1].set_title('Altitude')
        self.axes[1].grid(True, alpha=0.3)
        
        # Plot 3: Speed over time
        if len(self.time_history) > 0:
            self.axes[2].plot(
                list(self.time_history),
                list(self.speed_history),
                'r-', linewidth=1.5
            )
        self.axes[2].set_xlabel('Time (s)')
        self.axes[2].set_ylabel('Speed (kts)')
        self.axes[2].set_title('Airspeed')
        self.axes[2].grid(True, alpha=0.3)
        
        # Plot 4: Current state text
        self.axes[3].axis('off')
        status_text = f"""Current State:
Latitude: {state.get('latitude', 0):.4f}°
Longitude: {state.get('longitude', 0):.4f}°
Altitude: {state.get('altitude_ft', 0):.0f} ft
Speed: {state.get('speed_kts', 0):.0f} kts
Heading: {state.get('heading_deg', 0):.1f}°
Pitch: {state.get('pitch_deg', 0):.1f}°
Roll: {state.get('roll_deg', 0):.1f}°"""
        self.axes[3].text(0.1, 0.5, status_text, fontsize=10, 
                         verticalalignment='center', family='monospace')
        
        plt.tight_layout()
    
    def start_live_plot(self, flightgear_controller, update_interval=500):
        """
        Start live updating plot.
        
        Args:
            flightgear_controller: FlightGearController instance
            update_interval: Update interval in milliseconds
        """
        if self.running:
            return
        
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 10))
        self.axes = self.axes.flatten()
        
        self.running = True
        self.animation = animation.FuncAnimation(
            self.fig,
            lambda frame: self._update_plot(frame, flightgear_controller),
            interval=update_interval,
            blit=False,
            cache_frame_data=False  # Fix warning about unbounded cache
        )
        
        plt.show(block=False)
        print("Visualization started. Close the plot window to stop.")
    
    def stop(self):
        """Stop the visualization."""
        if self.animation:
            self.animation.event_source.stop()
        if self.fig:
            plt.close(self.fig)
        self.running = False
    
    def plot_flight_path(self):
        """
        Plot the complete flight path (static plot).
        Useful for viewing history after flight.
        """
        if len(self.latitude_history) < 2:
            print("Not enough data to plot flight path.")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Flight path
        axes[0, 0].plot(
            list(self.longitude_history),
            list(self.latitude_history),
            'b-', linewidth=1.5
        )
        axes[0, 0].plot(
            self.longitude_history[-1],
            self.latitude_history[-1],
            'ro', markersize=10
        )
        axes[0, 0].set_xlabel('Longitude (°)')
        axes[0, 0].set_ylabel('Latitude (°)')
        axes[0, 0].set_title('Flight Path')
        axes[0, 0].grid(True)
        
        # Altitude
        axes[0, 1].plot(list(self.time_history), list(self.altitude_history), 'g-')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Altitude (ft)')
        axes[0, 1].set_title('Altitude')
        axes[0, 1].grid(True)
        
        # Speed
        axes[1, 0].plot(list(self.time_history), list(self.speed_history), 'r-')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Speed (kts)')
        axes[1, 0].set_title('Airspeed')
        axes[1, 0].grid(True)
        
        # 3D flight path
        if len(self.altitude_history) > 0:
            ax_3d = fig.add_subplot(2, 2, 4, projection='3d')
            ax_3d.plot(
                list(self.longitude_history),
                list(self.latitude_history),
                list(self.altitude_history),
                'b-', linewidth=1.5
            )
            ax_3d.set_xlabel('Longitude (°)')
            ax_3d.set_ylabel('Latitude (°)')
            ax_3d.set_zlabel('Altitude (ft)')
            ax_3d.set_title('3D Flight Path')
        
        plt.tight_layout()
        plt.show()

