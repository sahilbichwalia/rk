import streamlit as st
import pandas as pd
import plotly.express as px
import psutil
import platform
import socket
import os
from datetime import datetime
from typing import Dict, Any

# Constants
GRID_EMISSION_FACTOR = 400  # gCO2/kWh (US average)
PUE_CLOUD = 1.2  # Power Usage Effectiveness for cloud data centers

# Page configuration
st.set_page_config(
    page_title="Cloud/Server Energy Monitor",
    page_icon="🌐",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #0e1117;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .alert-card {
        background-color: #2a3f5f;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .power-card {
        background-color: #1a1d24;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class SystemMonitor:
    """Comprehensive system monitoring with energy analytics"""
    
    @staticmethod
    def detect_environment() -> Dict[str, Any]:
        """Detect if running in cloud environment"""
        return {
            "is_streamlit_cloud": "STREAMLIT_SERVER_ADDRESS" in os.environ,
            "platform": platform.system(),
            "containerized": os.path.exists("/.dockerenv")
        }

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get all system metrics in a cloud-friendly way"""
        try:
            cpu_freq = psutil.cpu_freq().current if hasattr(psutil, "cpu_freq") else None
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()
            
            return {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "cpu_usage": psutil.cpu_percent(interval=1),
                "cpu_freq": cpu_freq,
                "memory_used": mem.used / (1024 ** 3),
                "memory_total": mem.total / (1024 ** 3),
                "memory_percent": mem.percent,
                "disk_used": disk.used / (1024 ** 3),
                "disk_total": disk.total / (1024 ** 3),
                "disk_percent": disk.percent,
                "network_sent": net_io.bytes_sent / (1024 ** 2),
                "network_recv": net_io.bytes_recv / (1024 ** 2)
            }
        except Exception as e:
            st.error(f"Metrics collection error: {str(e)}")
            return None

    @staticmethod
    def calculate_power(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate power usage from metrics"""
        if not metrics:
            return None
            
        try:
            # Dynamic power estimation
            cpu_power = (metrics["cpu_usage"]/100) * (metrics["cpu_freq"]/1000 if metrics["cpu_freq"] else 2.5) * 15
            mem_power = metrics["memory_used"] * 0.3  # 0.3W per GB
            disk_power = 5 if metrics["disk_percent"] > 50 else 2
            
            total_it_power = cpu_power + mem_power + disk_power
            total_power = total_it_power * PUE_CLOUD
            
            return {
                "cpu": round(cpu_power, 1),
                "memory": round(mem_power, 1),
                "disk": round(disk_power, 1),
                "total_it": round(total_it_power, 1),
                "total_facility": round(total_power, 1),
                "pue": PUE_CLOUD
            }
        except Exception as e:
            st.error(f"Power calculation error: {str(e)}")
            return None

    @staticmethod
    def calculate_emissions(power_w: float) -> Dict[str, Any]:
        """Calculate carbon emissions"""
        if not power_w:
            return None
            
        try:
            hourly_co2 = (power_w / 1000) * GRID_EMISSION_FACTOR
            return {
                "hourly": round(hourly_co2, 1),
                "daily": round(hourly_co2 * 24 / 1000, 2),
                "annual": round(hourly_co2 * 24 * 365 / 1000000, 3)
            }
        except Exception as e:
            st.error(f"Emission calculation error: {str(e)}")
            return None

def create_gauge(value: float, title: str, color: str) -> px.pie:
    """Create a gauge chart for metrics visualization"""
    fig = px.pie(
        values=[value, 100-value],
        names=['Used', 'Free'],
        hole=0.7,
        title=f"{title}: {value}%"
    )
    fig.update_traces(
        textinfo='none',
        marker=dict(colors=[color, '#333333'])
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=50, b=10, l=10, r=10),
        height=200
    )
    return fig

def main():
    """Main application function"""
    monitor = SystemMonitor()
    env = monitor.detect_environment()
    
    st.title("🌐 Cloud/Server Energy Monitoring Dashboard")
    
    # Environment awareness
    if env["is_streamlit_cloud"]:
        st.markdown("""
        <div class="alert-card">
            <h3>🛠️ Running in Cloud Environment</h3>
            <p>Some hardware metrics may be limited due to cloud virtualization</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize session state for metrics history
    if 'metrics_history' not in st.session_state:
        st.session_state.metrics_history = pd.DataFrame(columns=[
            'timestamp', 'cpu_usage', 'memory_percent', 'disk_percent',
            'cpu_power', 'mem_power', 'disk_power', 'total_power'
        ])
    
    # Get current metrics
    metrics = monitor.get_system_metrics()
    
    # Layout columns
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### System Metrics")
        
        if metrics:
            # Resource usage gauges
            st.plotly_chart(
                create_gauge(metrics["cpu_usage"], "CPU", "#1f77b4"),
                use_container_width=True
            )
            
            st.plotly_chart(
                create_gauge(metrics["memory_percent"], "Memory", "#ff7f0e"),
                use_container_width=True
            )
            
            st.plotly_chart(
                create_gauge(metrics["disk_percent"], "Disk", "#2ca02c"),
                use_container_width=True
            )
            
            # Network activity
            st.markdown("#### Network Activity")
            net_df = pd.DataFrame({
                "Direction": ["Sent", "Received"],
                "MB": [metrics["network_sent"], metrics["network_recv"]]
            })
            st.bar_chart(net_df.set_index("Direction"))
    
    with col2:
        st.markdown("### Power Analytics")
        
        if metrics:
            power = monitor.calculate_power(metrics)
            emissions = monitor.calculate_emissions(power["total_facility"] if power else None)
            
            if power:
                # Update metrics history
                new_row = {
                    'timestamp': metrics["timestamp"],
                    'cpu_usage': metrics["cpu_usage"],
                    'memory_percent': metrics["memory_percent"],
                    'disk_percent': metrics["disk_percent"],
                    'cpu_power': power["cpu"],
                    'mem_power': power["memory"],
                    'disk_power': power["disk"],
                    'total_power': power["total_facility"]
                }
                
                st.session_state.metrics_history = pd.concat([
                    st.session_state.metrics_history,
                    pd.DataFrame([new_row])
                ]).tail(60)  # Keep last 60 readings
                
                # Power metrics cards
                st.markdown("""
                <div class="power-card">
                    <h4>Power Consumption</h4>
                    <p>CPU: {cpu}W | Memory: {mem}W | Disk: {disk}W</p>
                    <p>Total IT Load: {it}W | Facility Power: {fac}W (PUE: {pue})</p>
                </div>
                """.format(
                    cpu=power["cpu"],
                    mem=power["memory"],
                    disk=power["disk"],
                    it=power["total_it"],
                    fac=power["total_facility"],
                    pue=power["pue"]
                ), unsafe_allow_html=True)
                
                # Emissions card
                if emissions:
                    st.markdown("""
                    <div class="power-card">
                        <h4>Carbon Emissions</h4>
                        <p>Current: {hourly}g CO₂/hour</p>
                        <p>Estimated Daily: {daily}kg | Annual: {annual} metric tons</p>
                    </div>
                    """.format(
                        hourly=emissions["hourly"],
                        daily=emissions["daily"],
                        annual=emissions["annual"]
                    ), unsafe_allow_html=True)
                
                # Anomaly detection
                if len(st.session_state.metrics_history) > 10:
                    avg_power = st.session_state.metrics_history['total_power'].mean()
                    current_power = power["total_facility"]
                    threshold = avg_power * 1.3  # 30% above average
                    
                    if current_power > threshold:
                        st.markdown("""
                        <div class="alert-card">
                            <h4>⚠️ Power Anomaly Detected</h4>
                            <p>Current: {current:.1f}W (Avg: {avg:.1f}W)</p>
                            <p>Potential inefficiency or workload spike detected</p>
                        </div>
                        """.format(current=current_power, avg=avg_power), unsafe_allow_html=True)
                
                # Power trend visualization
                if len(st.session_state.metrics_history) > 1:
                    st.markdown("#### Power Trend (Last 60 Readings)")
                    fig = px.line(
                        st.session_state.metrics_history,
                        x='timestamp',
                        y='total_power',
                        labels={'total_power': 'Total Power (W)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    # Cloud-specific notes
    if env["is_streamlit_cloud"]:
        st.info("""
        **Cloud Environment Notes:**
        - Power estimations are approximations based on container resource usage
        - Actual physical hardware metrics may differ
        - Anomaly detection compares against recent container activity patterns
        """)

if __name__ == "__main__":
    main()
