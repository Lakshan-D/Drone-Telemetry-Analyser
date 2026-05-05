"""
kpi_engine.py
Evaluates UAV telemetry data against EARHEART trial KPIs.
Based on EASA SORA operational requirements and UK CAA BVLOS guidance.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any


# ── KPI Thresholds ─────────────────────────────────────────────────────────────
# Based on EASA AMC RPAS.1309 and UK CAA CAP 722 BVLOS operational standards

KPI_THRESHOLDS = {
    "gps_accuracy": {
        "name": "GPS Positioning Accuracy",
        "metric": "hdop",
        "green":  2.0,    # HDOP < 2.0 = excellent
        "amber":  3.0,    # HDOP 2.0-3.0 = acceptable
        "basis":  "EASA AMC RPAS.1309 / ICAO Annex 10"
    },
    "gps_satellites": {
        "name": "GPS Satellite Coverage",
        "metric": "gps_satellites",
        "green":  8,      # >= 8 satellites = good
        "amber":  6,      # 6-7 = acceptable
        "basis":  "UK CAA CAP 722 BVLOS Navigation Requirements"
    },
    "signal_strength": {
        "name": "C2 Link Signal Strength",
        "metric": "signal_dbm",
        "green":  -75,    # > -75 dBm = strong
        "amber":  -85,    # -75 to -85 = acceptable
        "basis":  "EASA SORA OSO #10 — C2 Link Performance"
    },
    "battery_margin": {
        "name": "Battery Reserve Margin",
        "metric": "battery_pct",
        "green":  30,     # Never below 30% = safe
        "amber":  20,     # 20-30% = warning
        "basis":  "UK CAA CAP 722 / EASA UAS.SPEC.050"
    },
    "altitude_deviation": {
        "name": "Altitude Holding Accuracy",
        "metric": "altitude_m",
        "green":  5,      # Deviation < 5m = excellent
        "amber":  15,     # Deviation 5-15m = acceptable
        "basis":  "EASA SORA OSO #06 — Flight Termination System"
    },
    "speed_compliance": {
        "name": "Speed Limit Compliance",
        "metric": "speed_ms",
        "green":  25,     # Max authorised speed
        "amber":  28,     # Warning threshold
        "basis":  "EASA ConOps Speed Envelope"
    },
    "wind_envelope": {
        "name": "Wind Envelope Compliance",
        "metric": "wind_speed_ms",
        "green":  10,     # < 10 m/s = within envelope
        "amber":  12,     # 10-12 m/s = caution
        "basis":  "Manufacturer operating limits / EASA AMC"
    },
}


def evaluate_kpis(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Evaluate all KPIs against telemetry data.
    Returns list of KPI result dicts for display.
    """
    results = []

    for kpi_id, kpi in KPI_THRESHOLDS.items():
        col = kpi["metric"]
        if col not in df.columns:
            continue

        series = df[col].dropna()
        if len(series) == 0:
            continue

        if kpi_id == "gps_accuracy":
            # Lower HDOP is better
            val = series.mean()
            worst = series.max()
            pct_green = (series < kpi["green"]).mean() * 100
            if val < kpi["green"]:
                status = "PASS"
            elif val < kpi["amber"]:
                status = "WARNING"
            else:
                status = "FAIL"
            display_val = f"{val:.2f} (avg HDOP)"

        elif kpi_id == "gps_satellites":
            val = series.mean()
            worst = series.min()
            pct_green = (series >= kpi["green"]).mean() * 100
            if worst >= kpi["green"]:
                status = "PASS"
            elif worst >= kpi["amber"]:
                status = "WARNING"
            else:
                status = "FAIL"
            display_val = f"{val:.1f} avg | min {int(worst)}"

        elif kpi_id == "signal_strength":
            # Higher (less negative) is better
            val = series.mean()
            worst = series.min()
            pct_green = (series > kpi["green"]).mean() * 100
            if worst > kpi["amber"]:
                status = "PASS"
            elif worst > kpi["amber"] - 10:
                status = "WARNING"
            else:
                status = "FAIL"
            display_val = f"{val:.1f} dBm avg | min {worst:.1f}"

        elif kpi_id == "battery_margin":
            val = series.min()
            pct_green = (series >= kpi["green"]).mean() * 100
            if val >= kpi["green"]:
                status = "PASS"
            elif val >= kpi["amber"]:
                status = "WARNING"
            else:
                status = "FAIL"
            display_val = f"Min: {val:.1f}%"

        elif kpi_id == "altitude_deviation":
            target = series.median()
            deviation = (series - target).abs()
            val = deviation.mean()
            worst = deviation.max()
            pct_green = (deviation < kpi["green"]).mean() * 100
            if val < kpi["green"]:
                status = "PASS"
            elif val < kpi["amber"]:
                status = "WARNING"
            else:
                status = "FAIL"
            display_val = f"Avg dev: {val:.1f}m | Max: {worst:.1f}m"

        elif kpi_id == "speed_compliance":
            val = series.max()
            pct_green = (series <= kpi["green"]).mean() * 100
            if val <= kpi["green"]:
                status = "PASS"
            elif val <= kpi["amber"]:
                status = "WARNING"
            else:
                status = "FAIL"
            display_val = f"Max: {val:.1f} m/s"

        elif kpi_id == "wind_envelope":
            val = series.max()
            pct_green = (series <= kpi["green"]).mean() * 100
            if val <= kpi["green"]:
                status = "PASS"
            elif val <= kpi["amber"]:
                status = "WARNING"
            else:
                status = "FAIL"
            display_val = f"Max: {val:.1f} m/s"

        else:
            continue

        results.append({
            "KPI": kpi["name"],
            "Value": display_val,
            "% Time in Green": f"{pct_green:.1f}%",
            "Status": status,
            "Regulatory Basis": kpi["basis"]
        })

    return results


def compute_flight_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute high-level flight summary statistics."""
    duration_s  = len(df)
    duration_m  = duration_s / 60

    # Distance (approximate from GPS)
    dlat = df["latitude"].diff().fillna(0)
    dlon = df["longitude"].diff().fillna(0)
    dist_deg = np.sqrt(dlat**2 + dlon**2)
    dist_km  = dist_deg.sum() * 111  # rough degrees to km

    # Pass/warn/fail counts
    kpis = evaluate_kpis(df)
    passed  = sum(1 for k in kpis if k["Status"] == "PASS")
    warned  = sum(1 for k in kpis if k["Status"] == "WARNING")
    failed  = sum(1 for k in kpis if k["Status"] == "FAIL")

    # Overall readiness
    if failed == 0 and warned <= 1:
        readiness = "OPERATIONAL"
        readiness_colour = "green"
    elif failed == 0:
        readiness = "MARGINAL"
        readiness_colour = "orange"
    else:
        readiness = "NOT AIRWORTHY"
        readiness_colour = "red"

    return {
        "duration_mins": round(duration_m, 1),
        "distance_km": round(dist_km, 2),
        "max_altitude_m": round(df["altitude_m"].max(), 1),
        "avg_speed_ms": round(df["speed_ms"].mean(), 1),
        "min_battery_pct": round(df["battery_pct"].min(), 1),
        "avg_signal_dbm": round(df["signal_dbm"].mean(), 1),
        "kpi_pass": passed,
        "kpi_warn": warned,
        "kpi_fail": failed,
        "readiness": readiness,
        "readiness_colour": readiness_colour,
        "total_kpis": len(kpis),
    }


def detect_anomalies(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect anomalous events in telemetry data."""
    anomalies = []

    # GPS degradation
    gps_bad = df[df["gps_satellites"] < 6]
    if len(gps_bad) > 0:
        anomalies.append({
            "Time": str(gps_bad["timestamp"].iloc[0]),
            "Event": "GPS Degradation",
            "Detail": f"{len(gps_bad)}s below 6 satellites. Min: {gps_bad['gps_satellites'].min()}",
            "Severity": "HIGH",
            "EASA Reference": "SORA OSO #10"
        })

    # Signal loss
    signal_bad = df[df["signal_dbm"] < -85]
    if len(signal_bad) > 0:
        anomalies.append({
            "Time": str(signal_bad["timestamp"].iloc[0]),
            "Event": "C2 Link Degradation",
            "Detail": f"{len(signal_bad)}s below -85 dBm. Min: {signal_bad['signal_dbm'].min():.1f} dBm",
            "Severity": "HIGH",
            "EASA Reference": "SORA OSO #10"
        })

    # Altitude exceedance
    target_alt = df["altitude_m"].median()
    alt_dev = (df["altitude_m"] - target_alt).abs()
    alt_bad = df[alt_dev > 20]
    if len(alt_bad) > 0:
        anomalies.append({
            "Time": str(alt_bad["timestamp"].iloc[0]),
            "Event": "Altitude Deviation",
            "Detail": f"Max deviation: {alt_dev.max():.1f}m from planned altitude",
            "Severity": "MEDIUM",
            "EASA Reference": "SORA OSO #06"
        })

    # Battery warning
    battery_bad = df[df["battery_pct"] < 25]
    if len(battery_bad) > 0:
        anomalies.append({
            "Time": str(battery_bad["timestamp"].iloc[0]),
            "Event": "Low Battery Warning",
            "Detail": f"Battery below 25% for {len(battery_bad)}s. Min: {battery_bad['battery_pct'].min():.1f}%",
            "Severity": "MEDIUM",
            "EASA Reference": "UAS.SPEC.050"
        })

    # Speed exceedance
    speed_bad = df[df["speed_ms"] > 25]
    if len(speed_bad) > 0:
        anomalies.append({
            "Time": str(speed_bad["timestamp"].iloc[0]),
            "Event": "Speed Limit Exceedance",
            "Detail": f"Max speed: {speed_bad['speed_ms'].max():.1f} m/s. Duration: {len(speed_bad)}s",
            "Severity": "LOW",
            "EASA Reference": "ConOps Speed Envelope"
        })

    return anomalies
