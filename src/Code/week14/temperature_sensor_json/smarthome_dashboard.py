import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import json
import matplotlib.pyplot as plt
from collections import deque
import threading
import os
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

# =======================
# Configuration Section
# =======================

# Maximum number of data points to display
max_len = 50

# Deques for storing time-series data
timestamps = deque(maxlen=max_len)
indoor_temperatures = deque(maxlen=max_len)
indoor_humidities = deque(maxlen=max_len)
light_levels = deque(maxlen=max_len)
motion_detections = deque(maxlen=max_len)
door_window_status = deque(maxlen=max_len)
air_qualities = deque(maxlen=max_len)
energy_consumptions = deque(maxlen=max_len)

# Global variables
home_status = "NORMAL"
monitoring_active = True
security_mode = False
client = None
widgets = {}

# =======================
# MQTT Callback Functions
# =======================

def on_connect(client, userdata, flags, reason_code, properties=None):
    """Called when the client connects to the MQTT broker."""
    print(f"Connected with result code {reason_code}")
    client.subscribe("smarthome/sensor_data")

def on_message(client, userdata, msg):
    """Called when a new MQTT message is received."""
    global home_status, monitoring_active, security_mode, widgets
    
    try:
        data = json.loads(msg.payload.decode())
        print(f"Received data - Home Status: {data.get('home_status', 'UNKNOWN')}, "
              f"Monitoring: {data.get('monitoring_active', 'Unknown')}, "
              f"Security: {data.get('security_mode', 'Unknown')}")
        
        # Append received data to respective deques
        timestamps.append(data['timestamp'])
        indoor_temperatures.append(data['indoor_temperature_celsius'])
        indoor_humidities.append(data['indoor_humidity_percent'])
        light_levels.append(data['light_level_lux'])
        motion_detections.append(data['motion_detected'])
        door_window_status.append(data['door_window_open'])
        air_qualities.append(data['air_quality_index'])
        energy_consumptions.append(data['energy_consumption_kw'])
        
        # Update global variables
        home_status = data.get('home_status', home_status)
        monitoring_active = data.get('monitoring_active', monitoring_active)
        security_mode = data.get('security_mode', security_mode)
        
        # Update GUI status labels and buttons
        update_gui_elements()
        
    except Exception as e:
        print(f"Error processing message: {e}")

def update_gui_elements():
    """Update all GUI elements based on current state"""
    global widgets, home_status, monitoring_active, security_mode
    
    if not widgets:
        return
    
    try:
        # Update status label with color coding
        if home_status == "INTRUSION":
            status_color = "red"
        elif home_status == "ALERT":
            status_color = "orange"
        elif home_status == "WARNING":
            status_color = "darkorange"
        elif home_status == "SECURE":
            status_color = "blue"
        else:  # NORMAL
            status_color = "green"
        
        widgets['status_label'].config(text=f"Home Status: {home_status}", fg=status_color)
        
        monitoring_text = "ACTIVE" if monitoring_active else "INACTIVE"
        monitoring_color = "green" if monitoring_active else "red"
        widgets['monitoring_label'].config(text=f"Monitoring: {monitoring_text}", fg=monitoring_color)
        
        security_text = "ON" if security_mode else "OFF"
        security_color = "blue" if security_mode else "gray"
        widgets['security_label'].config(text=f"Security Mode: {security_text}", fg=security_color)
        
        # Update monitoring control buttons
        if monitoring_active:
            widgets['start_button'].config(state=tk.NORMAL, bg="gray")
            widgets['stop_button'].config(state=tk.NORMAL, bg="red")
        else:
            widgets['start_button'].config(state=tk.NORMAL, bg="green")
            widgets['stop_button'].config(state=tk.NORMAL, bg="gray")
        
        # Update security control buttons
        if security_mode:
            widgets['security_on_button'].config(state=tk.NORMAL, bg="gray")
            widgets['security_off_button'].config(state=tk.NORMAL, bg="red")
        else:
            widgets['security_on_button'].config(state=tk.NORMAL, bg="blue")
            widgets['security_off_button'].config(state=tk.NORMAL, bg="gray")
            
    except Exception as e:
        print(f"Error updating GUI: {e}")

# =======================
# Button Handlers
# =======================

def start_monitoring():
    """Publish message to start monitoring."""
    print("Button clicked: Start Monitoring")
    if client:
        client.publish("control/monitoring", "START")
        print("Published: START monitoring command")

def stop_monitoring():
    """Publish message to stop monitoring."""
    print("Button clicked: Stop Monitoring")
    if client:
        client.publish("control/monitoring", "STOP")
        print("Published: STOP monitoring command")

def security_on():
    """Activate security mode."""
    print("Button clicked: Security ON")
    if client:
        client.publish("control/security", "ON")
        print("Published: Security ON command")

def security_off():
    """Deactivate security mode."""
    print("Button clicked: Security OFF")
    if client:
        client.publish("control/security", "OFF")
        print("Published: Security OFF command")

# =======================
# Dashboard (GUI)
# =======================

def create_dashboard():
    """Create the main smart home dashboard UI with plots and controls."""
    global widgets
    
    root = tk.Tk()
    root.title("Smart Home Monitoring Dashboard")
    root.geometry("1600x1000")
    
    # Control section
    control_frame = tk.Frame(root)
    control_frame.pack(pady=10)
    
    # Status labels
    status_label = tk.Label(control_frame, text=f"Home Status: {home_status}", 
                           font=("Arial", 14, "bold"), fg="green")
    status_label.pack(side=tk.LEFT, padx=20)
    
    monitoring_text = "ACTIVE" if monitoring_active else "INACTIVE"
    monitoring_color = "green" if monitoring_active else "red"
    monitoring_label = tk.Label(control_frame, text=f"Monitoring: {monitoring_text}", 
                               font=("Arial", 12), fg=monitoring_color)
    monitoring_label.pack(side=tk.LEFT, padx=20)
    
    security_text = "ON" if security_mode else "OFF"
    security_color = "blue" if security_mode else "gray"
    security_label = tk.Label(control_frame, text=f"Security Mode: {security_text}", 
                             font=("Arial", 12), fg=security_color)
    security_label.pack(side=tk.LEFT, padx=20)
    
    # Monitoring control buttons
    if monitoring_active:
        start_state = tk.NORMAL
        start_bg = "gray"
        stop_state = tk.NORMAL
        stop_bg = "red"
    else:
        start_state = tk.NORMAL
        start_bg = "green"
        stop_state = tk.NORMAL
        stop_bg = "gray"
    
    start_button = tk.Button(control_frame, text="Start Monitoring", command=start_monitoring,
                            bg=start_bg, fg="white", font=("Arial", 10), padx=10, state=start_state)
    start_button.pack(side=tk.LEFT, padx=5)
    
    stop_button = tk.Button(control_frame, text="Stop Monitoring", command=stop_monitoring,
                           bg=stop_bg, fg="white", font=("Arial", 10), padx=10, state=stop_state)
    stop_button.pack(side=tk.LEFT, padx=5)
    
    # Security control buttons
    if security_mode:
        security_on_state = tk.NORMAL
        security_on_bg = "gray"
        security_off_state = tk.NORMAL
        security_off_bg = "red"
    else:
        security_on_state = tk.NORMAL
        security_on_bg = "blue"
        security_off_state = tk.NORMAL
        security_off_bg = "gray"
    
    security_on_button = tk.Button(control_frame, text="Security Mode ON", command=security_on,
                                 bg=security_on_bg, fg="white", font=("Arial", 10), padx=10, 
                                 state=security_on_state)
    security_on_button.pack(side=tk.LEFT, padx=5)
    
    security_off_button = tk.Button(control_frame, text="Security Mode OFF", command=security_off,
                                  bg=security_off_bg, fg="white", font=("Arial", 10), padx=10, 
                                  state=security_off_state)
    security_off_button.pack(side=tk.LEFT, padx=5)
    
    # เก็บ widgets ใน global variable
    widgets = {
        'status_label': status_label,
        'monitoring_label': monitoring_label,
        'security_label': security_label,
        'start_button': start_button,
        'stop_button': stop_button,
        'security_on_button': security_on_button,
        'security_off_button': security_off_button
    }
    
    print(f"Initial GUI state - Monitoring: {monitoring_active}, Security: {security_mode}")
    
    # Plot section using matplotlib - 8 subplots for 7 sensors + 1 summary
    fig = plt.Figure(figsize=(16, 12), dpi=100)
    
    # Indoor Temperature plot
    ax1 = fig.add_subplot(4, 2, 1)
    line1, = ax1.plot([], [], 'red', linewidth=2)
    ax1.set_ylabel('Temperature (°C)', color='red')
    ax1.set_title('Indoor Temperature')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='Comfort Zone')
    ax1.axhline(y=26, color='green', linestyle='--', alpha=0.7)
    ax1.legend()
    
    # Indoor Humidity plot
    ax2 = fig.add_subplot(4, 2, 2)
    line2, = ax2.plot([], [], 'cyan', linewidth=2)
    ax2.set_ylabel('Humidity (%)', color='cyan')
    ax2.set_title('Indoor Humidity')
    ax2.grid(True, alpha=0.3)
    
    # Light Level plot
    ax3 = fig.add_subplot(4, 2, 3)
    line3, = ax3.plot([], [], 'yellow', linewidth=2)
    ax3.set_ylabel('Light Level (Lux)', color='orange')
    ax3.set_title('Indoor Light Level')
    ax3.grid(True, alpha=0.3)
    
    # Motion & Door/Window Status plot
    ax4 = fig.add_subplot(4, 2, 4)
    line4_motion, = ax4.plot([], [], 'purple', linewidth=2, marker='o', markersize=4, label='Motion')
    line4_door, = ax4.plot([], [], 'brown', linewidth=2, marker='s', markersize=4, label='Door/Window')
    ax4.set_ylabel('Status (0=No/Closed, 1=Yes/Open)')
    ax4.set_title('Motion & Door/Window Status')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(-0.1, 1.1)
    
    # Air Quality plot
    ax5 = fig.add_subplot(4, 2, 5)
    line5, = ax5.plot([], [], 'green', linewidth=2)
    ax5.set_ylabel('Air Quality Index', color='green')
    ax5.set_title('Air Quality Monitor')
    ax5.axhline(y=50, color='green', linestyle='--', alpha=0.7, label='Good')
    ax5.axhline(y=100, color='orange', linestyle='--', alpha=0.7, label='Moderate')
    ax5.grid(True, alpha=0.3)
    ax5.legend()
    
    # Energy Consumption plot
    ax6 = fig.add_subplot(4, 2, 6)
    line6, = ax6.plot([], [], 'blue', linewidth=2)
    ax6.set_ylabel('Energy (kW)', color='blue')
    ax6.set_title('Energy Consumption')
    ax6.grid(True, alpha=0.3)
    
    # Home Summary plot
    ax7 = fig.add_subplot(4, 1, 4)
    ax7.set_title('Smart Home Status Summary')
    
    plt.tight_layout()
    
    # Embed plot in tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Plot update function
    def update_plot():
        if timestamps:
            x_range = range(len(timestamps))
            
            # Update all lines with new data
            line1.set_data(x_range, list(indoor_temperatures))
            line2.set_data(x_range, list(indoor_humidities))
            line3.set_data(x_range, list(light_levels))
            line4_motion.set_data(x_range, list(motion_detections))
            line4_door.set_data(x_range, list(door_window_status))
            line5.set_data(x_range, list(air_qualities))
            line6.set_data(x_range, list(energy_consumptions))
            
            # Update axis limits
            for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
                ax.set_xlim(0, max(1, len(timestamps) - 1))
            
            if indoor_temperatures:
                ax1.set_ylim(min(indoor_temperatures) - 2, max(indoor_temperatures) + 2)
            if indoor_humidities:
                ax2.set_ylim(0, 100)
            if light_levels:
                ax3.set_ylim(0, max(light_levels) + 100)
            if air_qualities:
                ax5.set_ylim(0, max(air_qualities) + 20)
            if energy_consumptions:
                ax6.set_ylim(0, max(energy_consumptions) + 0.5)
            
            # Update home summary
            ax7.clear()
            if home_status == "INTRUSION":
                status_color = 'red'
            elif home_status == "ALERT":
                status_color = 'orange'
            elif home_status == "WARNING":
                status_color = 'darkorange'
            elif home_status == "SECURE":
                status_color = 'blue'
            else:  # NORMAL
                status_color = 'green'
            
            ax7.text(0.5, 0.8, f'Home Status: {home_status}', transform=ax7.transAxes, 
                    fontsize=16, ha='center', va='center', color=status_color, weight='bold')
            
            if indoor_temperatures and energy_consumptions:
                latest_temp = indoor_temperatures[-1]
                latest_humidity = indoor_humidities[-1] if indoor_humidities else 0
                latest_energy = energy_consumptions[-1]
                latest_air_quality = air_qualities[-1] if air_qualities else 0
                latest_motion = "Detected" if motion_detections[-1] else "None" if motion_detections else "None"
                latest_door = "Open" if door_window_status[-1] else "Closed" if door_window_status else "Closed"
                
                ax7.text(0.15, 0.5, f'Temperature: {latest_temp}°C', transform=ax7.transAxes, 
                        fontsize=10, ha='center', va='center')
                ax7.text(0.35, 0.5, f'Humidity: {latest_humidity}%', transform=ax7.transAxes, 
                        fontsize=10, ha='center', va='center')
                ax7.text(0.55, 0.5, f'Energy: {latest_energy} kW', transform=ax7.transAxes, 
                        fontsize=10, ha='center', va='center')
                ax7.text(0.75, 0.5, f'Air Quality: {latest_air_quality}', transform=ax7.transAxes, 
                        fontsize=10, ha='center', va='center')
                
                ax7.text(0.25, 0.3, f'Motion: {latest_motion}', transform=ax7.transAxes, 
                        fontsize=10, ha='center', va='center')
                ax7.text(0.75, 0.3, f'Doors/Windows: {latest_door}', transform=ax7.transAxes, 
                        fontsize=10, ha='center', va='center')
                
                # Security status
                security_status = "🛡️ Security: ON" if security_mode else "🏠 Security: OFF"
                security_color = 'blue' if security_mode else 'gray'
                ax7.text(0.5, 0.1, security_status, transform=ax7.transAxes, 
                        fontsize=12, ha='center', va='center', color=security_color, weight='bold')
            
            ax7.set_title('Smart Home Status Summary')
            ax7.set_xlim(0, 1)
            ax7.set_ylim(0, 1)
            ax7.axis('off')
            
            canvas.draw()
        
        # Schedule the next update
        root.after(2000, update_plot)
    
    update_plot()
    
    return root, widgets

# =======================
# Main Program
# =======================

if __name__ == "__main__":
    # Path to TLS certificate files
    parent_dir = r"."
    ca_file = os.path.join(parent_dir, "ca.crt")
    cert_file = os.path.join(parent_dir, "client.crt")
    key_file = os.path.join(parent_dir, "client.key")
    
    # Start the dashboard
    root, widgets = create_dashboard()
    
    # Initialize MQTT client
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Set MQTT credentials
    client.username_pw_set('pk', 'YOUR_MQTT_PASSWORD')
    
    # Enable TLS security
    client.tls_set(
        ca_certs=ca_file,
        certfile=cert_file,
        keyfile=key_file
    )
    
    # Connect to broker
    client.connect("localhost", 8883, 60)
    
    # Start MQTT processing in a background thread
    mqtt_thread = threading.Thread(target=client.loop_forever, daemon=True)
    mqtt_thread.start()
    
    print("Smart Home Dashboard started. MQTT connection established.")
    
    # Start GUI main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.disconnect()
