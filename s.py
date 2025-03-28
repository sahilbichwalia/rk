import streamlit as st
import psutil
import platform
import time
import pandas as pd
import plotly.express as px
from datetime import datetime

# Constants
GRID_EMISSION_FACTOR = 500  # gCO2/kWh (global average)
PUE_CLOUD = 1.2  # Power Usage Effectiveness for cloud data centers

st.set_page_config(layout="wide")

class DataCenterMonitor:
    """Data Center Energy Monitoring System"""
    
    @staticmethod
    def get_live_metrics():
        """Collect real-time server metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_usage": cpu_percent,
            "memory_used": mem.used / (1024 ** 3),
            "memory_total": mem.total / (1024 ** 3),
            "disk_used": disk.used / (1024 ** 3),
            "disk_total": disk.total / (1024 ** 3)
        }

    @staticmethod
    def estimate_power(metrics):
        """Estimate power consumption"""
        # Dynamic power model for cloud servers
        cpu_power = metrics["cpu_usage"]/100 * 150  # 150W max TDP assumed
        mem_power = metrics["memory_used"] * 0.3    # 0.3W per GB
        disk_power = 10 if metrics["disk_used"] > 0 else 5
        
        it_power = cpu_power + mem_power + disk_power
        total_power = it_power * PUE_CLOUD
        
        return {
            "cpu_power": cpu_power,
            "mem_power": mem_power,
            "disk_power": disk_power,
            "it_power": it_power,
            "total_power": total_power,
            "cooling_overhead": total_power - it_power
        }

    @staticmethod
    def calculate_emissions(power_w):
        """Calculate carbon footprint"""
        hourly_co2 = (power_w / 1000) * GRID_EMISSION_FACTOR
        return {
            "hourly": hourly_co2,
            "daily": hourly_co2 * 24,
            "annual": hourly_co2 * 24 * 365
        }

# Initialize session state
if 'metrics_history' not in st.session_state:
    st.session_state.metrics_history = pd.DataFrame(columns=[
        'timestamp', 'cpu_usage', 'memory_used', 'disk_used',
        'cpu_power', 'mem_power', 'disk_power', 'total_power', 'co2_hourly'
    ])

# Dashboard UI
st.title("🌐 Data Center Energy Intelligence Dashboard")
st.markdown("""
**Addressing cloud infrastructure challenges:**  
Real-time power visibility • Anomaly detection • Carbon-aware scheduling
""")

# Main columns
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Live Power Metrics")
    placeholder = st.empty()
    
    # Anomaly detection section
    st.subheader("🚨 Energy Anomaly Detection")
    if len(st.session_state.metrics_history) > 10:
        avg_power = st.session_state.metrics_history['total_power'].mean()
        last_power = st.session_state.metrics_history['total_power'].iloc[-1]
        anomaly_threshold = avg_power * 1.3  # 30% above average
        
        if last_power > anomaly_threshold:
            st.error(f"⚠️ Power spike detected: {last_power:.1f}W (30% above normal)")
            st.progress(min(100, int((last_power/avg_power)*100)))
        else:
            st.success("✔️ Normal operation")
    else:
        st.info("Collecting baseline data...")

with col2:
    st.subheader("Power Trend Analysis")
    if not st.session_state.metrics_history.empty:
        fig = px.line(st.session_state.metrics_history, 
                     x='timestamp', y='total_power',
                     title="Total Power Consumption (W)")
        st.plotly_chart(fig, use_container_width=True)

# Continuous monitoring
monitor = DataCenterMonitor()

while True:
    # Get fresh metrics
    metrics = monitor.get_live_metrics()
    power = monitor.estimate_power(metrics)
    emissions = monitor.calculate_emissions(power["total_power"])
    
    # Update metrics history
    new_row = {
        **metrics,
        "cpu_power": power["cpu_power"],
        "mem_power": power["mem_power"],
        "disk_power": power["disk_power"],
        "total_power": power["total_power"],
        "co2_hourly": emissions["hourly"]
    }
    st.session_state.metrics_history = pd.concat([
        st.session_state.metrics_history,
        pd.DataFrame([new_row])
    ], ignore_index=True).tail(60)  # Keep last 60 readings
    
    # Update live metrics display
    with placeholder.container():
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        kpi1.metric("CPU Power", f"{power['cpu_power']:.1f}W", 
                   f"{metrics['cpu_usage']:.1f}% usage")
        kpi2.metric("Memory Power", f"{power['mem_power']:.1f}W", 
                   f"{metrics['memory_used']:.1f}/{metrics['memory_total']:.1f}GB")
        kpi3.metric("Total Power", f"{power['total_power']:.1f}W", 
                   f"PUE: {PUE_CLOUD:.2f}")
        kpi4.metric("CO₂ Emissions", f"{emissions['hourly']:.1f}g/h", 
                   f"{emissions['annual']/1000:.1f} kg/year")
    
    time.sleep(5)  # Refresh every 5 seconds
