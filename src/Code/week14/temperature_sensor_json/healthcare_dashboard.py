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
heart_rates = deque(maxlen=max_len)
systolic_pressures = deque(maxlen=max_len)
diastolic_pressures = deque(maxlen=max_len)
glucose_levels = deque(maxlen=max_len)
temperatures = deque(maxlen=max_len)
spo2_levels = deque(maxlen=max_len)

# Global variables
health_status = "NORMAL"
monitoring_active = True  # Default state
emergency_mode = False    # Default state
client = None
widgets = {}  # เพิ่ม global widgets

# =======================
# MQTT Callback Functions
# =======================

def on_connect(client, userdata, flags, reason_code, properties=None):
    """Called when the client connects to the MQTT broker."""
    print(f"Connected with result code {reason_code}")
    client.subscribe("healthcare/sensor_data")

def on_message(client, userdata, msg):
    """Called when a new MQTT message is received."""
    global health_status, monitoring_active, emergency_mode, widgets
    
    try:
        data = json.loads(msg.payload.decode())
        print(f"Received data - Health Status: {data.get('health_status', 'UNKNOWN')}, "
              f"Monitoring: {data.get('monitoring_active', 'Unknown')}, "
              f"Emergency: {data.get('emergency_mode', 'Unknown')}")
        
        # Append received data to respective deques
        timestamps.append(data['timestamp'])
        heart_rates.append(data['heart_rate_bpm'])
        systolic_pressures.append(data['blood_pressure_systolic'])
        diastolic_pressures.append(data['blood_pressure_diastolic'])
        glucose_levels.append(data['blood_glucose_mg_dl'])
        temperatures.append(data['body_temperature_celsius'])
        spo2_levels.append(data['blood_oxygen_spo2'])
        
        # Update global variables
        health_status = data.get('health_status', health_status)
        monitoring_active = data.get('monitoring_active', monitoring_active)
        emergency_mode = data.get('emergency_mode', emergency_mode)
        
        # Update GUI status labels and buttons
        update_gui_elements()
        
    except Exception as e:
        print(f"Error processing message: {e}")

def update_gui_elements():
    """Update all GUI elements based on current state"""
    global widgets, health_status, monitoring_active, emergency_mode
    
    if not widgets:
        return
    
    try:
        # Update status label with color coding
        status_color = "red" if health_status == "EMERGENCY" else "orange" if health_status == "ABNORMAL" else "green"
        widgets['status_label'].config(text=f"Health Status: {health_status}", fg=status_color)
        
        monitoring_text = "ACTIVE" if monitoring_active else "INACTIVE"
        monitoring_color = "green" if monitoring_active else "red"
        widgets['monitoring_label'].config(text=f"Monitoring: {monitoring_text}", fg=monitoring_color)
        
        # Update monitoring control buttons
        if monitoring_active:
            widgets['start_button'].config(state=tk.NORMAL, bg="gray")
            widgets['stop_button'].config(state=tk.NORMAL, bg="red")
            print("GUI Update: Monitoring ACTIVE - Start disabled, Stop enabled")
        else:
            widgets['start_button'].config(state=tk.NORMAL, bg="green")
            widgets['stop_button'].config(state=tk.NORMAL, bg="gray")
            print("GUI Update: Monitoring INACTIVE - Start enabled, Stop disabled")
        
        # Update emergency control buttons
        if emergency_mode:
            widgets['emergency_on_button'].config(state=tk.NORMAL, bg="gray")
            widgets['emergency_off_button'].config(state=tk.NORMAL, bg="red")
            print("GUI Update: Emergency ON - On disabled, Off enabled")
        else:
            widgets['emergency_on_button'].config(state=tk.NORMAL, bg="orange")
            widgets['emergency_off_button'].config(state=tk.NORMAL, bg="gray")
            print("GUI Update: Emergency OFF - On enabled, Off disabled")
            
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

def emergency_on():
    """Activate emergency mode."""
    print("Button clicked: Emergency ON")
    if client:
        client.publish("control/emergency", "ON")
        print("Published: Emergency ON command")

def emergency_off():
    """Deactivate emergency mode."""
    print("Button clicked: Emergency OFF")
    if client:
        client.publish("control/emergency", "OFF")
        print("Published: Emergency OFF command")

# =======================
# Dashboard (GUI)
# =======================

def create_dashboard():
    """Create the main healthcare dashboard UI with plots and controls."""
    global widgets
    
    root = tk.Tk()
    root.title("Healthcare Monitoring Dashboard")
    root.geometry("1400x1000")
    
    # Control section
    control_frame = tk.Frame(root)
    control_frame.pack(pady=10)
    
    # Status labels
    status_label = tk.Label(control_frame, text=f"Health Status: {health_status}", 
                           font=("Arial", 14, "bold"), fg="green")
    status_label.pack(side=tk.LEFT, padx=20)
    
    monitoring_text = "ACTIVE" if monitoring_active else "INACTIVE"
    monitoring_color = "green" if monitoring_active else "red"
    monitoring_label = tk.Label(control_frame, text=f"Monitoring: {monitoring_text}", 
                               font=("Arial", 12), fg=monitoring_color)
    monitoring_label.pack(side=tk.LEFT, padx=20)
    
    # Monitoring control buttons - ตั้ง initial state ให้ถูกต้อง
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
    
    # Emergency control buttons - ตั้ง initial state ให้ถูกต้อง
    if emergency_mode:
        emergency_on_state = tk.NORMAL
        emergency_on_bg = "gray"
        emergency_off_state = tk.NORMAL
        emergency_off_bg = "red"
    else:
        emergency_on_state = tk.NORMAL
        emergency_on_bg = "orange"
        emergency_off_state = tk.NORMAL
        emergency_off_bg = "gray"
    
    emergency_on_button = tk.Button(control_frame, text="Emergency Mode ON", command=emergency_on,
                                   bg=emergency_on_bg, fg="white", font=("Arial", 10), padx=10, 
                                   state=emergency_on_state)
    emergency_on_button.pack(side=tk.LEFT, padx=5)
    
    emergency_off_button = tk.Button(control_frame, text="Emergency Mode OFF", command=emergency_off,
                                    bg=emergency_off_bg, fg="white", font=("Arial", 10), padx=10, 
                                    state=emergency_off_state)
    emergency_off_button.pack(side=tk.LEFT, padx=5)
    
    # เก็บ widgets ใน global variable
    widgets = {
        'status_label': status_label,
        'monitoring_label': monitoring_label,
        'start_button': start_button,
        'stop_button': stop_button,
        'emergency_on_button': emergency_on_button,
        'emergency_off_button': emergency_off_button
    }
    
    print(f"Initial GUI state - Monitoring: {monitoring_active}, Emergency: {emergency_mode}")
    
    # Plot section using matplotlib - 6 subplots for 6 sensors
    fig = plt.Figure(figsize=(14, 10), dpi=100)
    
    # Heart Rate plot
    ax1 = fig.add_subplot(3, 2, 1)
    line1, = ax1.plot([], [], 'r-', linewidth=2)
    ax1.set_ylabel('Heart Rate (BPM)', color='r')
    ax1.set_title('Heart Rate Over Time')
    ax1.grid(True, alpha=0.3)
    
    # Blood Pressure plot
    ax2 = fig.add_subplot(3, 2, 2)
    line2_sys, = ax2.plot([], [], 'b-', linewidth=2, label='Systolic')
    line2_dia, = ax2.plot([], [], 'c-', linewidth=2, label='Diastolic')
    ax2.set_ylabel('Blood Pressure (mmHg)')
    ax2.set_title('Blood Pressure Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Blood Glucose plot
    ax3 = fig.add_subplot(3, 2, 3)
    line3, = ax3.plot([], [], 'g-', linewidth=2)
    ax3.set_ylabel('Glucose (mg/dL)', color='g')
    ax3.set_title('Blood Glucose Level Over Time')
    ax3.grid(True, alpha=0.3)
    
    # Body Temperature plot
    ax4 = fig.add_subplot(3, 2, 4)
    line4, = ax4.plot([], [], 'orange', linewidth=2)
    ax4.set_ylabel('Temperature (°C)', color='orange')
    ax4.set_title('Body Temperature Over Time')
    ax4.grid(True, alpha=0.3)
    
    # Blood Oxygen Saturation plot
    ax5 = fig.add_subplot(3, 2, 5)
    line5, = ax5.plot([], [], 'purple', linewidth=2)
    ax5.set_ylabel('SpO2 (%)', color='purple')
    ax5.set_title('Blood Oxygen Saturation Over Time')
    ax5.grid(True, alpha=0.3)
    
    # Summary/Status plot (can show overall health trend)
    ax6 = fig.add_subplot(3, 2, 6)
    ax6.text(0.5, 0.5, 'Health Summary', transform=ax6.transAxes, 
             fontsize=16, ha='center', va='center')
    ax6.set_title('Health Status Summary')
    
    plt.tight_layout()
    
    # Embed plot in tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Plot update function (called every 2 seconds)
    def update_plot():
        if timestamps:
            x_range = range(len(timestamps))
            
            # Update all lines with new data
            line1.set_data(x_range, list(heart_rates))
            line2_sys.set_data(x_range, list(systolic_pressures))
            line2_dia.set_data(x_range, list(diastolic_pressures))
            line3.set_data(x_range, list(glucose_levels))
            line4.set_data(x_range, list(temperatures))
            line5.set_data(x_range, list(spo2_levels))
            
            # Update axis limits
            for ax in [ax1, ax2, ax3, ax4, ax5]:
                ax.set_xlim(0, max(1, len(timestamps) - 1))
            
            if heart_rates:
                ax1.set_ylim(min(heart_rates) - 5, max(heart_rates) + 5)
            if systolic_pressures and diastolic_pressures:
                min_bp = min(min(diastolic_pressures), min(systolic_pressures)) - 5
                max_bp = max(max(diastolic_pressures), max(systolic_pressures)) + 5
                ax2.set_ylim(min_bp, max_bp)
            if glucose_levels:
                ax3.set_ylim(min(glucose_levels) - 10, max(glucose_levels) + 10)
            if temperatures:
                ax4.set_ylim(min(temperatures) - 0.5, max(temperatures) + 0.5)
            if spo2_levels:
                ax5.set_ylim(min(spo2_levels) - 2, max(spo2_levels) + 2)
            
            # Update X-tick labels for the bottom plots
            if len(timestamps) > 10:
                tick_indices = [i for i in range(0, len(timestamps), max(1, len(timestamps)//5))]
                if len(timestamps)-1 not in tick_indices:
                    tick_indices.append(len(timestamps)-1)
                
                for ax in [ax5, ax6]:  # Bottom row
                    ax.set_xticks(tick_indices)
                    ax.set_xticklabels([timestamps[i].split()[1] for i in tick_indices],
                                      rotation=45, ha='right')
            
            # Update health summary
            ax6.clear()
            status_color = 'red' if health_status == 'EMERGENCY' else 'orange' if health_status == 'ABNORMAL' else 'green'
            ax6.text(0.5, 0.7, f'Status: {health_status}', transform=ax6.transAxes, 
                    fontsize=14, ha='center', va='center', color=status_color, weight='bold')
            
            if heart_rates and glucose_levels and temperatures:
                latest_hr = heart_rates[-1]
                latest_glucose = glucose_levels[-1]
                latest_temp = temperatures[-1]
                ax6.text(0.5, 0.4, f'Latest Values:', transform=ax6.transAxes, 
                        fontsize=10, ha='center', va='center', weight='bold')
                ax6.text(0.5, 0.3, f'HR: {latest_hr} BPM', transform=ax6.transAxes, 
                        fontsize=9, ha='center', va='center')
                ax6.text(0.5, 0.2, f'Glucose: {latest_glucose} mg/dL', transform=ax6.transAxes, 
                        fontsize=9, ha='center', va='center')
                ax6.text(0.5, 0.1, f'Temp: {latest_temp}°C', transform=ax6.transAxes, 
                        fontsize=9, ha='center', va='center')
            
            ax6.set_title('Health Status Summary')
            
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
    
    print("Healthcare Dashboard started. MQTT connection established.")
    
    # Start GUI main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.disconnect()
