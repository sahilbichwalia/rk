import streamlit as st
import pandas as pd
import plotly.express as px
import psutil
import platform
import socket
import os
import getpass
import datetime
import uuid
from typing import Dict, Any

# Constants
GRID_EMISSION_FACTOR = 400  # gCO2/kWh (US average)
WATER_USAGE_IMPACT = 0.001

# Environment Detection
def detect_environment() -> Dict[str, Any]:
    """Detect if running in Streamlit Cloud or local/server"""
    env_info = {
        "is_streamlit_cloud": "STREAMLIT_SERVER_ADDRESS" in os.environ,
        "is_cloud": True if "STREAMLIT_SERVER_ADDRESS" in os.environ else None,
        "platform": platform.system(),
        "containerized": os.path.exists("/.dockerenv"),
        "cloud_provider": None
    }

    # Detect cloud providers
    try:
        if os.path.exists("/proc/1/cgroup") and any("docker" in line for line in open("/proc/1/cgroup")):
            env_info["containerized"] = True
            if os.path.exists("/etc/aws-hostname"):
                env_info["cloud_provider"] = "AWS"
            elif os.path.exists("/etc/gce-hostname"):
                env_info["cloud_provider"] = "GCP"
            elif "AZURE" in socket.gethostname():
                env_info["cloud_provider"] = "Azure"
    except:
        pass

    return env_info

# Page configuration
st.set_page_config(
    page_title="System Monitoring Dashboard",
    page_icon="🖥️",
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
    .gpu-card {
        background-color: #1a1d24;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .cloud-banner {
        background-color: #2a3f5f;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def get_system_info() -> Dict[str, Any]:
    """Get system information with cloud awareness"""
    env = detect_environment()
    info = {
        "Environment": "Streamlit Cloud" if env["is_streamlit_cloud"] else 
                     f"{env['cloud_provider']} Cloud" if env["cloud_provider"] else "Local Server",
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Platform": platform.platform(),
        "Containerized": env["containerized"],
        "Hostname": socket.gethostname(),
        "CPU Cores (Physical/Logical)": f"{psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}",
        "RAM Size (GB)": round(psutil.virtual_memory().total / (1024 ** 3), 2),
    }
    
    # Only include sensitive info if not in cloud
    if not env["is_streamlit_cloud"]:
        info.update({
            "User Name": getpass.getuser(),
            "MAC Address": ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                          for elements in range(0, 2*6, 8)][::-1])
        })
    return info

def get_cloud_metrics() -> Dict[str, Any]:
    """Get metrics that work well in cloud environments"""
    return {
        "CPU Usage (%)": psutil.cpu_percent(interval=1),
        "Memory Usage (%)": psutil.virtual_memory().percent,
        "Disk Usage (%)": psutil.disk_usage("/").percent,
        "Network IO (MB)": {
            "Sent": round(psutil.net_io_counters().bytes_sent / (1024 ** 2), 2),
            "Received": round(psutil.net_io_counters().bytes_recv / (1024 ** 2), 2)
        }
    }

def create_gauge(value: float, title: str, color: str):
    """Create a gauge chart"""
    fig = px.pie(
        values=[value, 100-value],
        names=['Used', 'Free'],
        hole=0.7,
        title=f"{title}: {value}%"
    )
    fig.update_traces(
        textinfo='none',
        marker=dict(colors=[color, '#d3d3d3'])
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=50, b=10, l=10, r=10),
        height=200
    )
    return fig

def main():
    env = detect_environment()
    
    # Environment banner
    if env["is_streamlit_cloud"]:
        st.markdown("""
        <div class="cloud-banner">
            <h3>🛠️ Running in Streamlit Cloud Environment</h3>
            <p>Some hardware metrics may be limited due to cloud virtualization</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.title("🖥️ Cloud/Server Monitoring Dashboard")
    
    # Get data
    system_info = get_system_info()
    metrics = get_cloud_metrics()
    
    # Layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Environment Info")
        env_df = pd.DataFrame({
            "Property": list(system_info.keys()),
            "Value": list(system_info.values())
        })
        st.dataframe(env_df, hide_index=True, use_container_width=True)
        
    with col2:
        st.markdown("### CPU Usage")
        st.plotly_chart(
            create_gauge(metrics["CPU Usage (%)"], "CPU", "#1f77b4"),
            use_container_width=True
        )
        
        st.markdown("### Memory Usage")
        st.plotly_chart(
            create_gauge(metrics["Memory Usage (%)"], "Memory", "#ff7f0e"),
            use_container_width=True
        )
        
    with col3:
        st.markdown("### Disk Usage")
        st.plotly_chart(
            create_gauge(metrics["Disk Usage (%)"], "Disk", "#2ca02c"),
            use_container_width=True
        )
        
        st.markdown("### Network Activity")
        net_df = pd.DataFrame({
            "Direction": ["Sent", "Received"],
            "MB": [
                metrics["Network IO (MB)"]["Sent"],
                metrics["Network IO (MB)"]["Received"]
            ]
        })
        st.bar_chart(net_df.set_index("Direction"))
    
    # Cloud-specific notes
    if env["is_streamlit_cloud"]:
        st.info("""
        **Note about Streamlit Cloud:**
        - Hardware-specific metrics (GPU, exact CPU details) are not available
        - Disk and memory measurements show container limits, not physical hardware
        - Network metrics are container-local
        """)

if __name__ == "__main__":
    main()
