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
max_len = 100

# Deques for storing time-series data
timestamps = deque(maxlen=max_len)
solar_powers = deque(maxlen=max_len)
generator_powers = deque(maxlen=max_len)
total_powers = deque(maxlen=max_len)
light_intensities = deque(maxlen=max_len)

# Global variables
generator_status = "OFF"
client = None

# =======================
# MQTT Callback Functions
# =======================

def on_connect(client, userdata, flags, reason_code, properties=None):
    """Called when the client connects to the MQTT broker."""
    print(f"Connected with result code {reason_code}")
    client.subscribe("sensor/sensor_value")

def on_message(client, userdata, msg):
    """Called when a new MQTT message is received."""
    global generator_status
    data = json.loads(msg.payload.decode())
    print(data)

    # Append received data to respective deques
    timestamps.append(data['timestamp'])
    solar_powers.append(data['solar_panel_power_watt'])
    generator_powers.append(data['generator_power_watt'])
    total_powers.append(data['total_power_watt'])
    light_intensities.append(data['light_intensity_lux'])
    generator_status = data.get('generator_status', generator_status)

    # Update GUI status label and buttons
    if 'status_label' in userdata and userdata['status_label']:
        userdata['status_label'].config(text=f"Generator Status: {generator_status}")
        if generator_status == "ON":
            userdata['on_button'].config(state=tk.DISABLED, bg="gray")
            userdata['off_button'].config(state=tk.NORMAL, bg="red")
        else:
            userdata['on_button'].config(state=tk.NORMAL, bg="green")
            userdata['off_button'].config(state=tk.DISABLED, bg="gray")

# =======================
# Button Handlers
# =======================

def turn_on_generator():
    """Publish message to turn ON the generator."""
    if client:
        client.publish("control/generator", "ON")
        print("Sending generator ON command")

def turn_off_generator():
    """Publish message to turn OFF the generator."""
    if client:
        client.publish("control/generator", "OFF")
        print("Sending generator OFF command")

# =======================
# Dashboard (GUI)
# =======================

def create_dashboard():
    """Create the main dashboard UI with plots and controls."""
    root = tk.Tk()
    root.title("Solar Power Monitoring Dashboard")
    root.geometry("1200x800")

    # Control section
    control_frame = tk.Frame(root)
    control_frame.pack(pady=10)

    status_label = tk.Label(control_frame, text=f"Generator Status: {generator_status}", font=("Arial", 14))
    status_label.pack(side=tk.LEFT, padx=20)

    on_button = tk.Button(control_frame, text="Start Generator", command=turn_on_generator,
                          bg="green", fg="white", font=("Arial", 12), padx=10)
    on_button.pack(side=tk.LEFT, padx=10)

    off_button = tk.Button(control_frame, text="Stop Generator", command=turn_off_generator,
                           bg="gray", fg="white", font=("Arial", 12), padx=10, state=tk.DISABLED)
    off_button.pack(side=tk.LEFT, padx=10)

    # Plot section using matplotlib
    fig = plt.Figure(figsize=(12, 8), dpi=100)

    # Light intensity plot
    ax1 = fig.add_subplot(3, 1, 1)
    line1, = ax1.plot([], [], 'y-', label='Light Intensity')
    ax1.set_ylabel('Light Intensity (lux)', color='y')
    ax1.set_title('Light Intensity Over Time')
    ax1.grid(True)

    # Solar power plot
    ax2 = fig.add_subplot(3, 1, 2)
    line2, = ax2.plot([], [], 'r-', label='Solar Power')
    ax2.set_ylabel('Solar Power (W)', color='r')
    ax2.set_title('Solar Power Over Time')
    ax2.grid(True)

    # Generator and total power plot
    ax3 = fig.add_subplot(3, 1, 3)
    line3, = ax3.plot([], [], 'g-', label='Generator Power')
    line4, = ax3.plot([], [], 'b-', label='Total Power')
    ax3.set_ylabel('Power (W)')
    ax3.set_xlabel('Timestamp')
    ax3.set_title('Generator and Total Power Over Time')
    ax3.legend()
    ax3.grid(True)

    # Embed plot in tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Plot update function (called every second)
    def update_plot():
        if timestamps:
            x_range = range(len(timestamps))

            # Update all lines with new data
            line1.set_data(x_range, list(light_intensities))
            line2.set_data(x_range, list(solar_powers))
            line3.set_data(x_range, list(generator_powers))
            line4.set_data(x_range, list(total_powers))

            # Update axis limits
            for ax in [ax1, ax2, ax3]:
                ax.set_xlim(0, len(timestamps) - 1)

            if light_intensities:
                ax1.set_ylim(0, max(light_intensities) * 1.1)
            if solar_powers:
                ax2.set_ylim(0, max(solar_powers) * 1.1)
            if total_powers:
                max_power = max(max(total_powers), max(generator_powers) if generator_powers else 0)
                ax3.set_ylim(0, max_power * 1.1)

            # Update X-tick labels
            if len(timestamps) > 10:
                tick_indices = [i for i in range(0, len(timestamps), len(timestamps)//10)]
                if len(timestamps)-1 not in tick_indices:
                    tick_indices.append(len(timestamps)-1)

                for ax in [ax1, ax2, ax3]:
                    ax.set_xticks(tick_indices)
                    if ax == ax3:
                        ax.set_xticklabels([timestamps[i].split()[1] for i in tick_indices],
                                           rotation=45, ha='right')
                    else:
                        ax.set_xticklabels([])

            canvas.draw()
        
        # Schedule the next update
        root.after(1000, update_plot)

    update_plot()

    # Return root window and UI components
    return root, status_label, on_button, off_button

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
    root, status_label, on_button, off_button = create_dashboard()

    # Initialize MQTT client
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    # Share tkinter widgets with MQTT callback
    client.user_data_set({
        'status_label': status_label,
        'on_button': on_button,
        'off_button': off_button
    })

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

    # Start GUI main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.disconnect()
