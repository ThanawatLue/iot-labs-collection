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
soil_moistures = deque(maxlen=max_len)
soil_temperatures = deque(maxlen=max_len)
air_temperatures = deque(maxlen=max_len)
air_humidities = deque(maxlen=max_len)
light_intensities = deque(maxlen=max_len)
ph_levels = deque(maxlen=max_len)
nutrient_levels = deque(maxlen=max_len)

# Global variables
farm_status = "OPTIMAL"
monitoring_active = True
irrigation_mode = False
client = None
widgets = {}

# =======================
# MQTT Callback Functions
# =======================

def on_connect(client, userdata, flags, reason_code, properties=None):
    """Called when the client connects to the MQTT broker."""
    print(f"Connected with result code {reason_code}")
    client.subscribe("smartfarm/sensor_data")

def on_message(client, userdata, msg):
    """Called when a new MQTT message is received."""
    global farm_status, monitoring_active, irrigation_mode, widgets
    
    try:
        data = json.loads(msg.payload.decode())
        print(f"Received data - Farm Status: {data.get('farm_status', 'UNKNOWN')}, "
              f"Monitoring: {data.get('monitoring_active', 'Unknown')}, "
              f"Irrigation: {data.get('irrigation_mode', 'Unknown')}")
        
        # Append received data to respective deques
        timestamps.append(data['timestamp'])
        soil_moistures.append(data['soil_moisture_percent'])
        soil_temperatures.append(data['soil_temperature_celsius'])
        air_temperatures.append(data['air_temperature_celsius'])
        air_humidities.append(data['air_humidity_percent'])
        light_intensities.append(data['light_intensity_lux'])
        ph_levels.append(data['ph_level'])
        nutrient_levels.append(data['nutrient_level_ppm'])
        
        # Update global variables
        farm_status = data.get('farm_status', farm_status)
        monitoring_active = data.get('monitoring_active', monitoring_active)
        irrigation_mode = data.get('irrigation_mode', irrigation_mode)
        
        # Update GUI status labels and buttons
        update_gui_elements()
        
    except Exception as e:
        print(f"Error processing message: {e}")

def update_gui_elements():
    """Update all GUI elements based on current state"""
    global widgets, farm_status, monitoring_active, irrigation_mode
    
    if not widgets:
        return
    
    try:
        # Update status label with color coding
        status_color = "red" if farm_status == "CRITICAL" else "orange" if farm_status == "WARNING" else "green"
        widgets['status_label'].config(text=f"Farm Status: {farm_status}", fg=status_color)
        
        monitoring_text = "ACTIVE" if monitoring_active else "INACTIVE"
        monitoring_color = "green" if monitoring_active else "red"
        widgets['monitoring_label'].config(text=f"Monitoring: {monitoring_text}", fg=monitoring_color)
        
        irrigation_text = "ON" if irrigation_mode else "OFF"
        irrigation_color = "blue" if irrigation_mode else "gray"
        widgets['irrigation_label'].config(text=f"Irrigation: {irrigation_text}", fg=irrigation_color)
        
        # Update monitoring control buttons
        if monitoring_active:
            widgets['start_button'].config(state=tk.NORMAL, bg="gray")
            widgets['stop_button'].config(state=tk.NORMAL, bg="red")
        else:
            widgets['start_button'].config(state=tk.NORMAL, bg="green")
            widgets['stop_button'].config(state=tk.NORMAL, bg="gray")
        
        # Update irrigation control buttons
        if irrigation_mode:
            widgets['irrigation_on_button'].config(state=tk.NORMAL, bg="gray")
            widgets['irrigation_off_button'].config(state=tk.NORMAL, bg="red")
        else:
            widgets['irrigation_on_button'].config(state=tk.NORMAL, bg="blue")
            widgets['irrigation_off_button'].config(state=tk.NORMAL, bg="gray")
            
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

def irrigation_on():
    """Activate irrigation system."""
    print("Button clicked: Irrigation ON")
    if client:
        client.publish("control/irrigation", "ON")
        print("Published: Irrigation ON command")

def irrigation_off():
    """Deactivate irrigation system."""
    print("Button clicked: Irrigation OFF")
    if client:
        client.publish("control/irrigation", "OFF")
        print("Published: Irrigation OFF command")

# =======================
# Dashboard (GUI)
# =======================

def create_dashboard():
    """Create the main smart farm dashboard UI with plots and controls."""
    global widgets
    
    root = tk.Tk()
    root.title("Smart Farm Monitoring Dashboard")
    root.geometry("1600x1000")
    
    # Control section
    control_frame = tk.Frame(root)
    control_frame.pack(pady=10)
    
    # Status labels
    status_label = tk.Label(control_frame, text=f"Farm Status: {farm_status}", 
                           font=("Arial", 14, "bold"), fg="green")
    status_label.pack(side=tk.LEFT, padx=20)
    
    monitoring_text = "ACTIVE" if monitoring_active else "INACTIVE"
    monitoring_color = "green" if monitoring_active else "red"
    monitoring_label = tk.Label(control_frame, text=f"Monitoring: {monitoring_text}", 
                               font=("Arial", 12), fg=monitoring_color)
    monitoring_label.pack(side=tk.LEFT, padx=20)
    
    irrigation_text = "ON" if irrigation_mode else "OFF"
    irrigation_color = "blue" if irrigation_mode else "gray"
    irrigation_label = tk.Label(control_frame, text=f"Irrigation: {irrigation_text}", 
                               font=("Arial", 12), fg=irrigation_color)
    irrigation_label.pack(side=tk.LEFT, padx=20)
    
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
    
    # Irrigation control buttons
    if irrigation_mode:
        irrigation_on_state = tk.NORMAL
        irrigation_on_bg = "gray"
        irrigation_off_state = tk.NORMAL
        irrigation_off_bg = "red"
    else:
        irrigation_on_state = tk.NORMAL
        irrigation_on_bg = "blue"
        irrigation_off_state = tk.NORMAL
        irrigation_off_bg = "gray"
    
    irrigation_on_button = tk.Button(control_frame, text="Irrigation ON", command=irrigation_on,
                                   bg=irrigation_on_bg, fg="white", font=("Arial", 10), padx=10, 
                                   state=irrigation_on_state)
    irrigation_on_button.pack(side=tk.LEFT, padx=5)
    
    irrigation_off_button = tk.Button(control_frame, text="Irrigation OFF", command=irrigation_off,
                                    bg=irrigation_off_bg, fg="white", font=("Arial", 10), padx=10, 
                                    state=irrigation_off_state)
    irrigation_off_button.pack(side=tk.LEFT, padx=5)
    
    # เก็บ widgets ใน global variable
    widgets = {
        'status_label': status_label,
        'monitoring_label': monitoring_label,
        'irrigation_label': irrigation_label,
        'start_button': start_button,
        'stop_button': stop_button,
        'irrigation_on_button': irrigation_on_button,
        'irrigation_off_button': irrigation_off_button
    }
    
    print(f"Initial GUI state - Monitoring: {monitoring_active}, Irrigation: {irrigation_mode}")
    
    # Plot section using matplotlib - 7 subplots for 7 sensors + 1 summary
    fig = plt.Figure(figsize=(16, 12), dpi=100)
    
    # Soil Moisture plot
    ax1 = fig.add_subplot(4, 2, 1)
    line1, = ax1.plot([], [], 'brown', linewidth=2)
    ax1.set_ylabel('Soil Moisture (%)', color='brown')
    ax1.set_title('Soil Moisture Over Time')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=30, color='red', linestyle='--', alpha=0.7, label='Critical Low')
    ax1.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Critical High')
    ax1.legend()
    
    # Temperature plot (Soil & Air)
    ax2 = fig.add_subplot(4, 2, 2)
    line2_soil, = ax2.plot([], [], 'saddlebrown', linewidth=2, label='Soil Temp')
    line2_air, = ax2.plot([], [], 'orange', linewidth=2, label='Air Temp')
    ax2.set_ylabel('Temperature (°C)')
    ax2.set_title('Temperature Monitoring')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Air Humidity plot
    ax3 = fig.add_subplot(4, 2, 3)
    line3, = ax3.plot([], [], 'cyan', linewidth=2)
    ax3.set_ylabel('Air Humidity (%)', color='cyan')
    ax3.set_title('Air Humidity Over Time')
    ax3.grid(True, alpha=0.3)
    
    # Light Intensity plot
    ax4 = fig.add_subplot(4, 2, 4)
    line4, = ax4.plot([], [], 'yellow', linewidth=2)
    ax4.set_ylabel('Light Intensity (Lux)', color='orange')
    ax4.set_title('Light Intensity Over Time')
    ax4.grid(True, alpha=0.3)
    
    # pH Level plot
    ax5 = fig.add_subplot(4, 2, 5)
    line5, = ax5.plot([], [], 'purple', linewidth=2)
    ax5.set_ylabel('pH Level', color='purple')
    ax5.set_title('Soil pH Level Over Time')
    ax5.axhline(y=6.0, color='green', linestyle='--', alpha=0.7, label='Optimal Range')
    ax5.axhline(y=7.5, color='green', linestyle='--', alpha=0.7)
    ax5.grid(True, alpha=0.3)
    ax5.legend()
    
    # Nutrient Level plot
    ax6 = fig.add_subplot(4, 2, 6)
    line6, = ax6.plot([], [], 'lime', linewidth=2)
    ax6.set_ylabel('Nutrient Level (ppm)', color='green')
    ax6.set_title('Nutrient Level Over Time')
    ax6.grid(True, alpha=0.3)
    
    # Farm Summary plot
    ax7 = fig.add_subplot(4, 1, 4)
    ax7.set_title('Smart Farm Status Summary')
    
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
            line1.set_data(x_range, list(soil_moistures))
            line2_soil.set_data(x_range, list(soil_temperatures))
            line2_air.set_data(x_range, list(air_temperatures))
            line3.set_data(x_range, list(air_humidities))
            line4.set_data(x_range, list(light_intensities))
            line5.set_data(x_range, list(ph_levels))
            line6.set_data(x_range, list(nutrient_levels))
            
            # Update axis limits
            for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
                ax.set_xlim(0, max(1, len(timestamps) - 1))
            
            if soil_moistures:
                ax1.set_ylim(0, 100)
            if soil_temperatures and air_temperatures:
                min_temp = min(min(soil_temperatures), min(air_temperatures)) - 2
                max_temp = max(max(soil_temperatures), max(air_temperatures)) + 2
                ax2.set_ylim(min_temp, max_temp)
            if air_humidities:
                ax3.set_ylim(0, 100)
            if light_intensities:
                ax4.set_ylim(0, max(light_intensities) + 5000)
            if ph_levels:
                ax5.set_ylim(4, 9)
            if nutrient_levels:
                ax6.set_ylim(0, max(nutrient_levels) + 50)
            
            # Update farm summary
            ax7.clear()
            status_color = 'red' if farm_status == 'CRITICAL' else 'orange' if farm_status == 'WARNING' else 'green'
            ax7.text(0.5, 0.8, f'Farm Status: {farm_status}', transform=ax7.transAxes, 
                    fontsize=16, ha='center', va='center', color=status_color, weight='bold')
            
            if soil_moistures and ph_levels and nutrient_levels:
                latest_moisture = soil_moistures[-1]
                latest_ph = ph_levels[-1]
                latest_nutrients = nutrient_levels[-1]
                latest_light = light_intensities[-1] if light_intensities else 0
                
                ax7.text(0.2, 0.5, f'Soil Moisture: {latest_moisture}%', transform=ax7.transAxes, 
                        fontsize=11, ha='center', va='center')
                ax7.text(0.4, 0.5, f'pH Level: {latest_ph}', transform=ax7.transAxes, 
                        fontsize=11, ha='center', va='center')
                ax7.text(0.6, 0.5, f'Nutrients: {latest_nutrients} ppm', transform=ax7.transAxes, 
                        fontsize=11, ha='center', va='center')
                ax7.text(0.8, 0.5, f'Light: {latest_light:,} Lux', transform=ax7.transAxes, 
                        fontsize=11, ha='center', va='center')
                
                # Irrigation status
                irrigation_status = "🚿 Irrigation: ON" if irrigation_mode else "🚿 Irrigation: OFF"
                irrigation_color = 'blue' if irrigation_mode else 'gray'
                ax7.text(0.5, 0.2, irrigation_status, transform=ax7.transAxes, 
                        fontsize=12, ha='center', va='center', color=irrigation_color, weight='bold')
            
            ax7.set_title('Smart Farm Status Summary')
            ax7.set_xlim(0, 1)
            ax7.set_ylim(0, 1)
            ax7.axis('off')
            
            canvas.draw()
        
        # Schedule the next update
        root.after(3000, update_plot)
    
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
    
    print("Smart Farm Dashboard started. MQTT connection established.")
    
    # Start GUI main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.disconnect()
