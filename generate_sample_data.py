"""
generate_sample_data.py
Generates realistic sample UAV telemetry CSV files for demonstration.
Run this once to create sample data: python generate_sample_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_flight_log(filename, duration_mins=30, anomaly=False):
    """Generate a realistic UAV BVLOS flight telemetry log."""
    np.random.seed(42 if not anomaly else 99)
    
    hz = 1  # 1 sample per second
    n = duration_mins * 60
    timestamps = [datetime(2026, 5, 1, 9, 0, 0) + timedelta(seconds=i) for i in range(n)]

    # GPS coordinates (route across UK Midlands)
    lat_base = 52.400 + np.linspace(0, 0.15, n)
    lon_base = -1.500 + np.linspace(0, 0.20, n)
    lat = lat_base + np.random.normal(0, 0.0001, n)
    lon = lon_base + np.random.normal(0, 0.0001, n)

    # Altitude (m AGL)
    altitude = 120 + np.random.normal(0, 2, n)
    if anomaly:
        # Sudden altitude drop at minute 15
        altitude[900:960] = np.linspace(120, 45, 60)
        altitude[960:1020] = np.linspace(45, 120, 60)

    # Speed (m/s)
    speed = 18 + np.random.normal(0, 1.5, n)
    speed = np.clip(speed, 0, 35)

    # Battery (%)
    battery = np.linspace(95, 25, n) + np.random.normal(0, 0.5, n)
    battery = np.clip(battery, 0, 100)
    if anomaly:
        # Rapid battery drain anomaly at minute 20
        battery[1200:] = battery[1200:] - 15

    # GPS satellites
    satellites = np.random.randint(10, 18, n).astype(float)
    if anomaly:
        # GPS degradation
        satellites[600:720] = np.random.randint(4, 7, 120)

    # HDOP (horizontal dilution of precision — lower is better, <2.0 is good)
    hdop = 1.2 + np.random.normal(0, 0.15, n)
    hdop = np.clip(hdop, 0.8, 5.0)
    if anomaly:
        hdop[600:720] = np.random.uniform(3.5, 5.0, 120)

    # Signal strength (dBm — less negative is better, >-80 acceptable)
    signal = -65 + np.random.normal(0, 5, n)
    if anomaly:
        # Signal loss event
        signal[1500:1560] = np.random.uniform(-95, -90, 60)

    # Pitch, roll, yaw (degrees)
    pitch = np.random.normal(2, 1.5, n)
    roll  = np.random.normal(0, 1.5, n)
    yaw   = np.linspace(0, 180, n) + np.random.normal(0, 2, n)

    # Wind speed (m/s)
    wind = 4 + np.random.normal(0, 1.5, n)
    wind = np.clip(wind, 0, 15)

    # Temperature (C)
    temp = 12 + np.random.normal(0, 1, n)

    df = pd.DataFrame({
        "timestamp":    timestamps,
        "latitude":     np.round(lat, 6),
        "longitude":    np.round(lon, 6),
        "altitude_m":   np.round(altitude, 1),
        "speed_ms":     np.round(speed, 2),
        "battery_pct":  np.round(battery, 1),
        "gps_satellites": satellites.astype(int),
        "hdop":         np.round(hdop, 2),
        "signal_dbm":   np.round(signal, 1),
        "pitch_deg":    np.round(pitch, 2),
        "roll_deg":     np.round(roll, 2),
        "yaw_deg":      np.round(yaw % 360, 2),
        "wind_speed_ms": np.round(wind, 2),
        "temperature_c": np.round(temp, 1),
    })

    os.makedirs("data/sample_logs", exist_ok=True)
    df.to_csv(f"data/sample_logs/{filename}", index=False)
    print(f"Generated: data/sample_logs/{filename} ({len(df)} records)")
    return df


if __name__ == "__main__":
    generate_flight_log("flight_nominal_20260501.csv",   duration_mins=30, anomaly=False)
    generate_flight_log("flight_anomaly_20260502.csv",   duration_mins=30, anomaly=True)
    generate_flight_log("flight_nominal_20260503.csv",   duration_mins=25, anomaly=False)
    print("\nSample data generated. Run: streamlit run app.py")
