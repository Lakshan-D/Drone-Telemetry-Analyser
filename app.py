import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime
import os
from utils.kpi_engine import evaluate_kpis, compute_flight_summary, detect_anomalies

st.set_page_config(
    page_title="EARHEART | Drone Telemetry Analyser",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Dark Mission Control Theme ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Global dark background */
    .stApp { background-color: #050d1a; color: #c8d8e8; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #070f1f; border-right: 1px solid #0a2a4a; }
    [data-testid="stSidebar"] * { color: #8ab4d4 !important; }
    [data-testid="stSidebar"] .stSelectbox label, 
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stSlider label { color: #4a9eca !important; font-size: 0.8rem !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; }

    /* Headers */
    h1, h2, h3 { color: #4ae4f0 !important; }
    
    /* Main title block */
    .mission-header {
        background: linear-gradient(135deg, #050d1a 0%, #0a1628 50%, #050d1a 100%);
        border: 1px solid #0d3a6e;
        border-left: 4px solid #00d4ff;
        padding: 20px 28px;
        margin-bottom: 24px;
        border-radius: 4px;
    }
    .mission-title {
        font-size: 1.9rem;
        font-weight: 800;
        color: #00d4ff !important;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-family: 'Courier New', monospace;
        margin: 0;
    }
    .mission-subtitle {
        font-size: 0.82rem;
        color: #4a7a9b;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-top: 4px;
    }
    .mission-id {
        font-size: 0.75rem;
        color: #00d4ff;
        font-family: 'Courier New', monospace;
        margin-top: 8px;
        opacity: 0.7;
    }

    /* Status badges */
    .badge-operational { background: linear-gradient(90deg, #0a2a0a, #1a4a1a); color: #00ff88; border: 1px solid #00ff88; padding: 6px 18px; border-radius: 3px; font-family: monospace; font-weight: 700; letter-spacing: 0.1em; font-size: 0.9rem; }
    .badge-marginal    { background: linear-gradient(90deg, #2a1a0a, #4a2a0a); color: #ffaa00; border: 1px solid #ffaa00; padding: 6px 18px; border-radius: 3px; font-family: monospace; font-weight: 700; letter-spacing: 0.1em; font-size: 0.9rem; }
    .badge-notairworthy{ background: linear-gradient(90deg, #2a0a0a, #4a0a0a); color: #ff3333; border: 1px solid #ff3333; padding: 6px 18px; border-radius: 3px; font-family: monospace; font-weight: 700; letter-spacing: 0.1em; font-size: 0.9rem; }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #070f1f, #0a1628);
        border: 1px solid #0d3a6e;
        border-top: 2px solid #00d4ff;
        border-radius: 4px;
        padding: 14px 18px;
        text-align: center;
    }
    .metric-label { font-size: 0.65rem; color: #4a7a9b; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 6px; }
    .metric-value { font-size: 1.6rem; font-weight: 800; color: #00d4ff; font-family: 'Courier New', monospace; }
    .metric-unit  { font-size: 0.7rem; color: #4a9eca; margin-top: 2px; }

    /* KPI status pills */
    .kpi-pass { color: #00ff88; font-weight: 700; font-family: monospace; }
    .kpi-warn { color: #ffaa00; font-weight: 700; font-family: monospace; }
    .kpi-fail { color: #ff3333; font-weight: 700; font-family: monospace; }

    /* Section dividers */
    .section-label {
        font-size: 0.7rem;
        color: #00d4ff;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        font-family: 'Courier New', monospace;
        border-bottom: 1px solid #0d3a6e;
        padding-bottom: 6px;
        margin: 20px 0 14px 0;
    }

    /* Anomaly cards */
    .anomaly-high   { border-left: 3px solid #ff3333; background: #1a0505; padding: 10px 14px; margin: 6px 0; border-radius: 3px; }
    .anomaly-medium { border-left: 3px solid #ffaa00; background: #1a1005; padding: 10px 14px; margin: 6px 0; border-radius: 3px; }
    .anomaly-low    { border-left: 3px solid #4ae4f0; background: #05101a; padding: 10px 14px; margin: 6px 0; border-radius: 3px; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: #070f1f; border-bottom: 1px solid #0d3a6e; gap: 4px; }
    .stTabs [data-baseweb="tab"] { background: transparent; color: #4a7a9b !important; border: 1px solid transparent; border-radius: 3px 3px 0 0; font-family: 'Courier New', monospace; font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; padding: 8px 18px; }
    .stTabs [aria-selected="true"] { background: #0a1628 !important; color: #00d4ff !important; border-color: #0d3a6e !important; border-bottom-color: #0a1628 !important; }

    /* Dataframe */
    [data-testid="stDataFrame"] { border: 1px solid #0d3a6e; }

    /* Footer */
    .mission-footer { font-size: 0.65rem; color: #1a3a5c; text-align: center; margin-top: 2rem; letter-spacing: 0.1em; font-family: monospace; text-transform: uppercase; }

    /* Plotly charts — dark bg */
    .js-plotly-plot { border: 1px solid #0d3a6e; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

PLOTLY_THEME = dict(
    paper_bgcolor="#070f1f",
    plot_bgcolor="#050d1a",
    font=dict(color="#8ab4d4", family="Courier New"),
    gridcolor="#0d2a4a",
    title_font=dict(color="#00d4ff", size=13),
)


def dark_fig(fig, height=380):
    fig.update_layout(
        paper_bgcolor="#070f1f",
        plot_bgcolor="#050d1a",
        font=dict(color="#8ab4d4", family="Courier New", size=11),
        height=height,
        margin=dict(l=50, r=20, t=50, b=40),
        legend=dict(bgcolor="#070f1f", bordercolor="#0d3a6e", borderwidth=1),
    )
    fig.update_xaxes(gridcolor="#0d2a4a", zerolinecolor="#0d2a4a", tickfont=dict(color="#4a7a9b"))
    fig.update_yaxes(gridcolor="#0d2a4a", zerolinecolor="#0d2a4a", tickfont=dict(color="#4a7a9b"))
    return fig


def metric_card(label, value, unit=""):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-unit">{unit}</div>
    </div>
    """


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### DATA INPUT")
    data_source = st.radio("Source", ["Sample Data", "Upload CSV"], label_visibility="collapsed")

    df = None

    if data_source == "Upload CSV":
        uploaded = st.file_uploader("Upload telemetry CSV", type=["csv"])
        if uploaded:
            df = pd.read_csv(uploaded, parse_dates=["timestamp"])
            st.success(f"{len(df)} records loaded")
    else:
        sample_dir = "data/sample_logs"
        if not os.path.exists(sample_dir) or len(os.listdir(sample_dir)) == 0:
            st.warning("Run: python generate_sample_data.py")
        else:
            files = sorted(os.listdir(sample_dir))
            selected = st.selectbox("Flight Log", files)
            df = pd.read_csv(f"{sample_dir}/{selected}", parse_dates=["timestamp"])
            st.caption(f"{len(df)} records")

    st.markdown("---")
    st.markdown("### MISSION DETAILS")
    mission_name   = st.text_input("Mission ID", "EARHEART-TRIAL-001")
    operator       = st.text_input("Operator", "BCU Research Team")
    drone_model    = st.text_input("Platform", "Fixed Wing BVLOS")
    trial_location = st.text_input("Location", "West Midlands, UK")

    st.markdown("---")
    st.markdown("### SYSTEM")
    st.caption(f"Session: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("Framework: EASA SORA / UK CAA CAP 722")
    st.caption("Project: EU EARHEART")

# ── Header ────────────────────────────────────────────────────────────────────
ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
st.markdown(f"""
<div class="mission-header">
    <div class="mission-title">🛸 EARHEART — Drone Telemetry Analyser</div>
    <div class="mission-subtitle">Independent BVLOS flight performance evaluation system</div>
    <div class="mission-id">MISSION: {mission_name} &nbsp;|&nbsp; OPERATOR: {operator} &nbsp;|&nbsp; SESSION: {ts}</div>
</div>
""", unsafe_allow_html=True)

# ── No data ───────────────────────────────────────────────────────────────────
if df is None:
    st.markdown('<div class="section-label">System Ready — Awaiting Data</div>', unsafe_allow_html=True)
    st.info("Load a flight log from the sidebar to begin evaluation.")
    st.code("python generate_sample_data.py  # generate sample logs")
    st.stop()

# ── Compute ───────────────────────────────────────────────────────────────────
summary   = compute_flight_summary(df)
kpis      = evaluate_kpis(df)
anomalies = detect_anomalies(df)
time_col  = df["timestamp"] if "timestamp" in df.columns else pd.RangeIndex(len(df))

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "OVERVIEW", "KPI ASSESSMENT", "SENSOR DATA", "ANOMALIES", "EXPORT"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-label">Mission Status</div>', unsafe_allow_html=True)

    badge_map = {
        "OPERATIONAL":   "badge-operational",
        "MARGINAL":      "badge-marginal",
        "NOT AIRWORTHY": "badge-notairworthy"
    }
    st.markdown(
        f'<span class="{badge_map[summary["readiness"]]}">{summary["readiness"]}</span>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-label">Flight Metrics</div>', unsafe_allow_html=True)

    cols = st.columns(6)
    metrics = [
        ("Duration", summary["duration_mins"], "MIN"),
        ("Distance", summary["distance_km"], "KM"),
        ("Max Alt", summary["max_altitude_m"], "M AGL"),
        ("Avg Speed", summary["avg_speed_ms"], "M/S"),
        ("Min Battery", summary["min_battery_pct"], "%"),
        ("Avg Signal", summary["avg_signal_dbm"], "DBM"),
    ]
    for col, (label, value, unit) in zip(cols, metrics):
        col.markdown(metric_card(label, value, unit), unsafe_allow_html=True)

    st.markdown('<div class="section-label">KPI Summary</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    k1.markdown(metric_card("KPIs Passed", f"{summary['kpi_pass']}/{summary['total_kpis']}", "GREEN ZONE"), unsafe_allow_html=True)
    k2.markdown(metric_card("Warnings", summary['kpi_warn'], "AMBER ZONE"), unsafe_allow_html=True)
    k3.markdown(metric_card("Failed", summary['kpi_fail'], "RED ZONE"), unsafe_allow_html=True)

    st.markdown('<div class="section-label">Flight Path</div>', unsafe_allow_html=True)

    if "latitude" in df.columns:
        fig_map = px.scatter_mapbox(
            df, lat="latitude", lon="longitude",
            color="altitude_m", color_continuous_scale=["#003366", "#0066cc", "#00d4ff", "#00ffcc"],
            mapbox_style="carto-darkmatter",
            zoom=11,
            labels={"altitude_m": "Alt (m)"}
        )
        fig_map.update_layout(
            paper_bgcolor="#070f1f",
            height=420,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_colorbar=dict(tickfont=dict(color="#8ab4d4"), title=dict(text="Alt (m)", font=dict(color="#00d4ff")))
        )
        st.plotly_chart(fig_map, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — KPI ASSESSMENT
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-label">KPI Evaluation — EASA SORA Standard</div>', unsafe_allow_html=True)

    for k in kpis:
        status = k["Status"]
        colour = "#00ff88" if status == "PASS" else "#ffaa00" if status == "WARNING" else "#ff3333"
        bg     = "#05100a" if status == "PASS" else "#10090a" if status == "FAIL" else "#0d0900"
        border = "#003a15" if status == "PASS" else "#3a0505" if status == "FAIL" else "#3a2000"

        st.markdown(f"""
        <div style="background:{bg}; border:1px solid {border}; border-left:3px solid {colour}; 
                    padding:12px 18px; margin:6px 0; border-radius:3px; display:flex; 
                    justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
                <div style="font-size:0.7rem; color:#4a7a9b; letter-spacing:0.1em; text-transform:uppercase; font-family:monospace;">{k['Regulatory Basis']}</div>
                <div style="font-size:1rem; color:#c8d8e8; font-weight:600; margin-top:2px;">{k['KPI']}</div>
                <div style="font-size:0.85rem; color:#8ab4d4; margin-top:2px; font-family:monospace;">{k['Value']}</div>
            </div>
            <div style="text-align:right;">
                <div style="color:{colour}; font-weight:800; font-family:monospace; font-size:1rem; letter-spacing:0.1em;">{status}</div>
                <div style="font-size:0.75rem; color:#4a7a9b; margin-top:2px;">{k['% Time in Green']} in green</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Performance Radar</div>', unsafe_allow_html=True)

    kpi_scores = [float(k["% Time in Green"].replace("%", "")) for k in kpis]
    kpi_labels = [k["KPI"] for k in kpis]

    fig_radar = go.Figure(data=go.Scatterpolar(
        r=kpi_scores + [kpi_scores[0]],
        theta=kpi_labels + [kpi_labels[0]],
        fill="toself",
        fillcolor="rgba(0, 212, 255, 0.08)",
        line=dict(color="#00d4ff", width=2),
        marker=dict(color="#00d4ff", size=6),
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(color="#4a7a9b"), gridcolor="#0d2a4a"),
            angularaxis=dict(tickfont=dict(color="#8ab4d4", size=10), gridcolor="#0d2a4a"),
            bgcolor="#050d1a",
        ),
        paper_bgcolor="#070f1f",
        height=450,
        margin=dict(l=60, r=60, t=40, b=40),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — SENSOR DATA
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-label">Altitude and Speed</div>', unsafe_allow_html=True)

    fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                          subplot_titles=("ALTITUDE (m AGL)", "SPEED (m/s)"),
                          vertical_spacing=0.12)
    fig1.add_trace(go.Scatter(x=time_col, y=df["altitude_m"], name="Altitude",
                               line=dict(color="#00d4ff", width=1.5)), row=1, col=1)
    fig1.add_hline(y=120, line_dash="dash", line_color="#ffaa00",
                   annotation_text="Planned", annotation_font_color="#ffaa00", row=1, col=1)
    fig1.add_trace(go.Scatter(x=time_col, y=df["speed_ms"], name="Speed",
                               line=dict(color="#00ffcc", width=1.5)), row=2, col=1)
    fig1.add_hline(y=25, line_dash="dash", line_color="#ff3333",
                   annotation_text="Limit", annotation_font_color="#ff3333", row=2, col=1)
    st.plotly_chart(dark_fig(fig1), use_container_width=True)

    st.markdown('<div class="section-label">GPS and Signal Quality</div>', unsafe_allow_html=True)

    fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                          subplot_titles=("GPS SATELLITES", "C2 LINK SIGNAL (dBm)"),
                          vertical_spacing=0.12)
    fig2.add_trace(go.Scatter(x=time_col, y=df["gps_satellites"], name="Satellites",
                               line=dict(color="#00ff88", width=1.5),
                               fill="tozeroy", fillcolor="rgba(0,255,136,0.05)"), row=1, col=1)
    fig2.add_hline(y=6, line_dash="dash", line_color="#ff3333",
                   annotation_text="Min", annotation_font_color="#ff3333", row=1, col=1)
    fig2.add_trace(go.Scatter(x=time_col, y=df["signal_dbm"], name="Signal",
                               line=dict(color="#a855f7", width=1.5)), row=2, col=1)
    fig2.add_hline(y=-85, line_dash="dash", line_color="#ff3333",
                   annotation_text="Min", annotation_font_color="#ff3333", row=2, col=1)
    st.plotly_chart(dark_fig(fig2), use_container_width=True)

    st.markdown('<div class="section-label">Battery and Wind</div>', unsafe_allow_html=True)

    fig3 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                          subplot_titles=("BATTERY (%)", "WIND SPEED (m/s)"),
                          vertical_spacing=0.12)
    fig3.add_trace(go.Scatter(x=time_col, y=df["battery_pct"], name="Battery",
                               line=dict(color="#ff6b00", width=1.5),
                               fill="tozeroy", fillcolor="rgba(255,107,0,0.08)"), row=1, col=1)
    fig3.add_hline(y=20, line_dash="dash", line_color="#ff3333",
                   annotation_text="Min Reserve", annotation_font_color="#ff3333", row=1, col=1)
    if "wind_speed_ms" in df.columns:
        fig3.add_trace(go.Scatter(x=time_col, y=df["wind_speed_ms"], name="Wind",
                                   line=dict(color="#4ae4f0", width=1.5)), row=2, col=1)
        fig3.add_hline(y=10, line_dash="dash", line_color="#ffaa00",
                       annotation_text="Op Limit", annotation_font_color="#ffaa00", row=2, col=1)
    st.plotly_chart(dark_fig(fig3), use_container_width=True)

    st.markdown('<div class="section-label">GPS Accuracy (HDOP)</div>', unsafe_allow_html=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=time_col, y=df["hdop"],
                               line=dict(color="#ff3366", width=1.5),
                               fill="tozeroy", fillcolor="rgba(255,51,102,0.05)"))
    fig4.add_hline(y=2.0, line_dash="dash", line_color="#ffaa00", annotation_text="Acceptable")
    fig4.add_hline(y=3.0, line_dash="dash", line_color="#ff3333", annotation_text="Max Limit")
    fig4.update_layout(yaxis_title="HDOP (lower=better)")
    st.plotly_chart(dark_fig(fig4, height=300), use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — ANOMALIES
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-label">Anomaly Detection Log</div>', unsafe_allow_html=True)

    if not anomalies:
        st.markdown("""
        <div style="background:#051a0a; border:1px solid #003a15; border-left:3px solid #00ff88; 
                    padding:16px 20px; border-radius:3px; font-family:monospace; color:#00ff88;">
            ALL CLEAR — No anomalies detected. All parameters within acceptable limits.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:#1a0505; border:1px solid #3a0505; border-left:3px solid #ff3333; 
                    padding:12px 20px; border-radius:3px; font-family:monospace; color:#ff3333; margin-bottom:12px;">
            WARNING — {len(anomalies)} anomalous event(s) detected
        </div>
        """, unsafe_allow_html=True)

        sev_colours = {"HIGH": "#ff3333", "MEDIUM": "#ffaa00", "LOW": "#4ae4f0"}
        sev_bg      = {"HIGH": "#1a0505",  "MEDIUM": "#1a1005",  "LOW": "#05101a"}

        for a in anomalies:
            c = sev_colours.get(a["Severity"], "#8ab4d4")
            bg = sev_bg.get(a["Severity"], "#070f1f")
            st.markdown(f"""
            <div style="background:{bg}; border:1px solid #1a2a3a; border-left:3px solid {c}; 
                        padding:14px 18px; margin:8px 0; border-radius:3px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                    <div>
                        <span style="color:{c}; font-weight:800; font-family:monospace; font-size:0.8rem; letter-spacing:0.1em;">{a['Severity']}</span>
                        <span style="color:#c8d8e8; font-weight:600; font-size:1rem; margin-left:12px;">{a['Event']}</span>
                    </div>
                    <div style="font-size:0.7rem; color:#4a7a9b; font-family:monospace;">{a['EASA Reference']}</div>
                </div>
                <div style="font-size:0.85rem; color:#8ab4d4; margin-top:8px; font-family:monospace;">{a['Detail']}</div>
                <div style="font-size:0.7rem; color:#4a7a9b; margin-top:4px;">{a['Time']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Recommendations</div>', unsafe_allow_html=True)
    if not anomalies:
        st.markdown('<p style="color:#00ff88; font-family:monospace; font-size:0.85rem;">Platform performance nominal. Cleared for next trial sortie.</p>', unsafe_allow_html=True)
    else:
        for a in anomalies:
            if a["Severity"] == "HIGH":
                st.markdown(f'<p style="color:#ff3333; font-family:monospace; font-size:0.82rem;">[ HIGH ] {a["Event"]}: Review before next flight. Ref: {a["EASA Reference"]}</p>', unsafe_allow_html=True)
            elif a["Severity"] == "MEDIUM":
                st.markdown(f'<p style="color:#ffaa00; font-family:monospace; font-size:0.82rem;">[ MED  ] {a["Event"]}: Monitor and log. Ref: {a["EASA Reference"]}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color:#4ae4f0; font-family:monospace; font-size:0.82rem;">[ LOW  ] {a["Event"]}: Note for report. Ref: {a["EASA Reference"]}</p>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — EXPORT
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-label">Export Assessment Report</div>', unsafe_allow_html=True)

    report_data = {
        "mission": {
            "name": mission_name,
            "operator": operator,
            "platform": drone_model,
            "location": trial_location,
            "generated": datetime.now().isoformat(),
        },
        "summary": summary,
        "kpis": kpis,
        "anomalies": anomalies,
        "framework": "EASA SORA / UK CAA CAP 722",
        "project": "EU EARHEART — BVLOS Trial Evaluation"
    }

    col1, col2 = st.columns(2)
    col1.markdown(f'<p style="color:#8ab4d4; font-family:monospace; font-size:0.82rem;">MISSION: {mission_name}<br>OPERATOR: {operator}<br>PLATFORM: {drone_model}<br>LOCATION: {trial_location}</p>', unsafe_allow_html=True)
    col2.markdown(f'<p style="color:#8ab4d4; font-family:monospace; font-size:0.82rem;">READINESS: <span style="color:{"#00ff88" if summary["readiness"]=="OPERATIONAL" else "#ffaa00"}">{summary["readiness"]}</span><br>KPIs PASSED: {summary["kpi_pass"]}/{summary["total_kpis"]}<br>ANOMALIES: {len(anomalies)}<br>GENERATED: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.download_button(
        "Download Evaluation Report (JSON)",
        data=json.dumps(report_data, indent=2, default=str),
        file_name=f"EARHEART_Evaluation_{mission_name.replace(' ', '_')}.json",
        mime="application/json"
    )

    st.markdown('<p style="color:#1a3a5c; font-size:0.75rem; font-family:monospace; margin-top:8px;">JSON format — compatible with digital twin platforms, regulatory submission systems, and consortium reporting tools.</p>', unsafe_allow_html=True)

st.markdown(
    '<p class="mission-footer">EARHEART Drone Telemetry Analyser — Lakshan Divakar — Brunel University London — EU EARHEART Project</p>',
    unsafe_allow_html=True
)
