# IoT Labs Collection

Collection of embedded systems and IoT lab projects covering sensor input, device control, dashboards, MQTT messaging, and simulation workflows.

This repository is a portfolio of hands-on experiments rather than one production application. It shows progression from basic GPIO-style logic to distributed MQTT systems with monitoring and alerting patterns.

## Featured Labs

### Flood Control With MQTT

Water-level monitoring and pump-control simulation with remote manual override.

- Publishes sensor state over MQTT.
- Supports command messages for manual intervention.
- Demonstrates the control-loop pattern used in small automation systems.

### Smart Home Monitoring Dashboard

Dashboard concept for indoor environment monitoring.

- Tracks temperature, humidity, light, motion, air quality, and energy-style telemetry.
- Uses local visualization patterns for real-time status review.

### Remote Patient Monitoring Simulation

Healthcare-style telemetry simulation for vital signs.

- Tracks heart rate, SpO2, and body temperature.
- Demonstrates threshold-based alert logic.

## Lab Topics

- Basic GPIO control
- Traffic light state machines
- Stopwatch and interrupt logic
- Smart irrigation
- Rotary encoder input
- MQTT publish/subscribe
- Secure messaging concepts
- Local dashboard visualization
- Sensor simulation

## Repository Structure

- `src/` - source code and lab scripts
- `mqtt/` - MQTT-specific experiments
- `docs/` - supporting lab notes, reports, or diagrams

## Tech Stack

- Python
- MQTT / Paho MQTT
- Tkinter
- Matplotlib
- SQLite
- Raspberry Pi / ESP32 / Arduino concepts

## How To Review

Start with the folders under `src/` and `mqtt/`. Each lab is intended to be read independently as a small experiment. For a hiring review, the MQTT flood-control and monitoring-dashboard work best represent the applied automation direction.

## Status

Educational lab collection. Some projects are simulations, while others are intended to map to physical device workflows.
