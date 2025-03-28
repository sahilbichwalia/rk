import streamlit as st
import psutil
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# Constants
GRID_EMISSION_FACTOR = 500  # gCO2/kWh
PUE_CLOUD = 1.2  # Power Usage Effectiveness

# Configure Streamlit
st.set_page_config(layout="wide")
st.title("🌍 Data Center Energy Monitor")

class EnergyMonitor:
    @staticmethod
    def get_metrics():
        """Get system metrics without terminal dependencies"""
        try:
            return {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "cpu": psutil.cpu_percent(interval=1),
                "memory": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage('/').percent,
                "cpu_freq": psutil.cpu_freq().current if hasattr(psutil, "cpu_freq") else 2500
            }
        except:
            return None

    @staticmethod
    def calculate_power(metrics):
        """Calculate power usage"""
        if not metrics:
            return None
        
        cpu_power = (metrics["cpu"]/100) * (metrics["cpu_freq"]/1000) * 10
        mem_power = metrics["memory"]/100 * 5
        disk_power = 2 if metrics["disk"] > 50 else 1
        
        return {
            "cpu": cpu_power,
            "memory": mem_power,
            "disk": disk_power,
            "total": cpu_power + mem_power + disk_power,
            "facility": (cpu_power + mem_power + disk_power) * PUE_CLOUD
        }

    @staticmethod
    def calculate_co2(power):
        """Calculate CO2 emissions"""
        if not power:
            return None
        return (power["facility"]/1000) * GRID_EMISSION_FACTOR

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'time', 'cpu', 'memory', 'disk', 'power', 'co2'
    ])

# Dashboard layout
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Live Metrics")
    metrics_placeholder = st.empty()
    alert_placeholder = st.empty()

with col2:
    st.header("Trend Analysis")
    chart_placeholder = st.empty()

# Main update loop
while True:
    # Get current metrics
    metrics = EnergyMonitor.get_metrics()
    
    if metrics:
        power = EnergyMonitor.calculate_power(metrics)
        co2 = EnergyMonitor.calculate_co2(power)
        
        # Update session data
        new_row = {
            'time': metrics["timestamp"],
            'cpu': metrics["cpu"],
            'memory': metrics["memory"],
            'disk': metrics["disk"],
            'power': power["total"] if power else 0,
            'co2': co2 if co2 else 0
        }
        
        st.session_state.data = pd.concat([
            st.session_state.data,
            pd.DataFrame([new_row])
        ]).tail(30)  # Keep last 30 readings
        
        # Update metrics display
        with metrics_placeholder.container():
            if power:
                st.metric("CPU Power", f"{power['cpu']:.1f}W", f"{metrics['cpu']:.1f}%")
                st.metric("Memory Power", f"{power['memory']:.1f}W", f"{metrics['memory']:.1f}%")
                st.metric("Total Power", f"{power['total']:.1f}W", f"PUE: {PUE_CLOUD}")
                st.metric("CO₂ Emissions", f"{co2:.1f}g/h" if co2 else "N/A")
        
        # Update alert system
        with alert_placeholder.container():
            if len(st.session_state.data) > 5:
                avg_power = st.session_state.data['power'].mean()
                current_power = power["total"] if power else 0
                if current_power > avg_power * 1.3:
                    st.error("Power spike detected!")
                else:
                    st.success("Normal operation")
        
        # Update chart
        with chart_placeholder.container():
            if len(st.session_state.data) > 1:
                fig = px.line(st.session_state.data, x='time', y='power')
                st.plotly_chart(fig, use_container_width=True)
    
    # Wait before next update
    time.sleep(5)
    st.experimental_rerun()
