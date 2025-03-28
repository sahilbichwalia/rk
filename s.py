import streamlit as st
import pandas as pd
import plotly.express as px
import psutil
import platform
import socket
import getpass
import datetime
import uuid
import GPUtil

# Constants
GRID_EMISSION_FACTOR = 400  # gCO2/kWh (US average)
WATER_USAGE_IMPACT = 0.001  # Placeholder for water usage impact

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
    .stMetric {
        background-color: #0e1117;
        border-radius: 10px;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

def get_system_info():
    """Get system information"""
    return {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Kernel Version": platform.release(),
        "Architecture": platform.architecture()[0],
        "Machine Type": platform.machine(),
        "Processor": platform.processor(),
        "CPU Cores (Physical/Logical)": f"{psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}",
        "RAM Size (GB)": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "Host Name": socket.gethostname(),
        "User Name": getpass.getuser(),
        "MAC Address": ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 8)][::-1])
    }

def get_cpu_usage():
    """Get CPU metrics"""
    freq = psutil.cpu_freq()
    return {
        "CPU Usage (%)": psutil.cpu_percent(interval=1),
        "CPU Frequency (MHz)": freq.current if freq else "N/A",
        "Per Core Usage": psutil.cpu_percent(interval=1, percpu=True)
    }

def get_memory_usage():
    """Get memory metrics"""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "Memory Usage (%)": mem.percent,
        "Total Memory (GB)": round(mem.total / (1024 ** 3), 2),
        "Used Memory (GB)": round(mem.used / (1024 ** 3), 2),
        "Swap Usage (%)": swap.percent
    }

def get_disk_usage():
    """Get disk metrics"""
    disk = psutil.disk_usage("/")
    io = psutil.disk_io_counters()
    return {
        "Total Disk Space (GB)": round(disk.total / (1024 ** 3), 2),
        "Used Disk Space (GB)": round(disk.used / (1024 ** 3), 2),
        "Free Disk Space (GB)": round(disk.free / (1024 ** 3), 2),
        "Disk Usage (%)": round((disk.used / disk.total) * 100, 2),
        "Disk Read (MB)": round(io.read_bytes / (1024 ** 2), 2) if io else 0,
        "Disk Write (MB)": round(io.write_bytes / (1024 ** 2), 2) if io else 0
    }

def get_network_info():
    """Get network metrics"""
    net_io = psutil.net_io_counters()
    return {
        "IP Address": socket.gethostbyname(socket.gethostname()),
        "Total Data Sent (MB)": round(net_io.bytes_sent / (1024 ** 2), 2),
        "Total Data Received (MB)": round(net_io.bytes_recv / (1024 ** 2), 2),
        "Packets Sent": net_io.packets_sent,
        "Packets Received": net_io.packets_recv
    }

def get_gpu_info():
    """Get GPU metrics if available"""
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return {"GPU": "No GPU Detected"}
        
        gpu_data = {}
        for gpu in gpus:
            gpu_data[gpu.name] = {
                "GPU Load (%)": gpu.load * 100,
                "GPU Memory Usage (%)": gpu.memoryUtil * 100,
                "GPU Temperature (°C)": gpu.temperature
            }
        return gpu_data
    except:
        return {"GPU": "Monitoring Not Available"}

def get_system_boot_time():
    """Get system boot time"""
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    return {"Last Boot Time": boot_time.strftime("%Y-%m-%d %H:%M:%S")}

def calculate_energy_metrics():
    """Calculate energy and environmental metrics"""
    # Example values - replace with actual measurements if available
    it_power = 100  # Watts (estimated IT equipment power)
    pue = 1.5  # Power Usage Effectiveness
    
    total_power = it_power * pue
    cooling_overhead = total_power - it_power
    carbon_hourly = (it_power / 1000) * GRID_EMISSION_FACTOR
    
    return {
        "IT Equipment Power (W)": it_power,
        "Total Facility Power (W)": total_power,
        "Cooling & Overhead Power (W)": cooling_overhead,
        "Power Usage Effectiveness (PUE)": pue,
        "Sustainable Use Effectiveness (SUE)": round((total_power + WATER_USAGE_IMPACT) / it_power, 2),
        "Carbon Intensity (gCO2/hour)": round(carbon_hourly, 2),
        "Estimated Annual CO2 Emissions (kgCO2/year)": round((carbon_hourly * 24 * 365) / 1000, 2)
    }

def create_gauge(value, title, color):
    """Helper function to create gauge charts"""
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
    st.title("🖥️ Real-time System Monitoring Dashboard")
    
    # Get all data
    system_info = get_system_info()
    cpu_usage = get_cpu_usage()
    memory_usage = get_memory_usage()
    disk_usage = get_disk_usage()
    network_info = get_network_info()
    gpu_info = get_gpu_info()
    boot_time = get_system_boot_time()
    energy_metrics = calculate_energy_metrics()
    
    # Create columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### System Information")
        st.markdown(f"""
        <div class="metric-card">
            <p><b>OS:</b> {system_info['OS']} {system_info['OS Version']}</p>
            <p><b>Kernel:</b> {system_info['Kernel Version']}</p>
            <p><b>Architecture:</b> {system_info['Architecture']}</p>
            <p><b>CPU:</b> {system_info['Processor']}</p>
            <p><b>Cores:</b> {system_info['CPU Cores (Physical/Logical)']}</p>
            <p><b>RAM:</b> {system_info['RAM Size (GB)']} GB</p>
            <p><b>Last Boot:</b> {boot_time['Last Boot Time']}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("### CPU & Memory")
        st.plotly_chart(
            create_gauge(
                cpu_usage['CPU Usage (%)'],
                "CPU Usage",
                '#1f77b4'
            ),
            use_container_width=True
        )
        
        st.plotly_chart(
            create_gauge(
                memory_usage['Memory Usage (%)'],
                "Memory Usage",
                '#ff7f0e'
            ),
            use_container_width=True
        )
        
    with col3:
        st.markdown("### Disk & Network")
        st.plotly_chart(
            create_gauge(
                disk_usage['Disk Usage (%)'],
                "Disk Usage",
                '#2ca02c'
            ),
            use_container_width=True
        )
        
        st.markdown(f"""
        <div class="metric-card">
            <p><b>IP Address:</b> {network_info['IP Address']}</p>
            <p><b>Data Sent:</b> {network_info['Total Data Sent (MB)']} MB</p>
            <p><b>Data Received:</b> {network_info['Total Data Received (MB)']} MB</p>
        </div>
        """, unsafe_allow_html=True)
    
    # GPU Information
    if "No GPU Detected" not in str(gpu_info) and "Monitoring Not Available" not in str(gpu_info):
        st.markdown("### GPU Information")
        gpu_cols = st.columns(len(gpu_info))
        
        for idx, (gpu_name, metrics) in enumerate(gpu_info.items()):
            with gpu_cols[idx]:
                st.markdown(f"""
                <div class="gpu-card">
                    <h4>{gpu_name}</h4>
                    <p><b>Load:</b> {metrics['GPU Load (%)']}%</p>
                    <p><b>Memory:</b> {metrics['GPU Memory Usage (%)']}%</p>
                    <p><b>Temp:</b> {metrics['GPU Temperature (°C)']}°C</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Energy Metrics
    st.markdown("### Energy Metrics")
    energy_col1, energy_col2, energy_col3 = st.columns(3)
    
    with energy_col1:
        st.metric("IT Equipment Power", f"{energy_metrics['IT Equipment Power (W)']} W")
        st.metric("Total Facility Power", f"{energy_metrics['Total Facility Power (W)']} W")
    
    with energy_col2:
        st.metric("PUE", f"{energy_metrics['Power Usage Effectiveness (PUE)']}")
        st.metric("SUE", f"{energy_metrics['Sustainable Use Effectiveness (SUE)']}")
    
    with energy_col3:
        st.metric("CO2/hour", f"{energy_metrics['Carbon Intensity (gCO2/hour)']} g")
        st.metric("Annual CO2", f"{energy_metrics['Estimated Annual CO2 Emissions (kgCO2/year)']} kg")
    
    # Data tables
    with st.expander("View Raw Data"):
        tab1, tab2, tab3 = st.tabs(["System Info", "Performance", "Energy"])
        
        with tab1:
            st.dataframe(pd.DataFrame([system_info]))
        
        with tab2:
            st.dataframe(pd.DataFrame([{
                **cpu_usage,
                **memory_usage,
                **disk_usage,
                **network_info
            }]))
        
        with tab3:
            st.dataframe(pd.DataFrame([energy_metrics]))

if __name__ == "__main__":
    main()
