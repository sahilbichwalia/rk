import streamlit as st
import pandas as pd
import plotly.express as px
from your_monitoring_script import (get_system_info, get_cpu_usage, 
                                  get_memory_usage, get_disk_usage,
                                  get_network_info, get_gpu_info,
                                  get_system_boot_time, calculate_energy_metrics)

# Page configuration
st.set_page_config(
    page_title="System Monitoring Dashboard",
    page_icon="🖥️",
    layout="wide"
)

# Custom CSS for better styling
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
</style>
""", unsafe_allow_html=True)

# Main dashboard layout
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
        # CPU Gauge
        st.plotly_chart(
            px.pie(
                values=[cpu_usage['CPU Usage (%)'], 
                names=["CPU Usage"],
                hole=0.7,
                title=f"CPU Usage: {cpu_usage['CPU Usage (%)']}%"
            ).update_traces(
                textinfo='none',
                marker=dict(colors=['#1f77b4', '#d3d3d3'])
            ).update_layout(
                showlegend=False,
                margin=dict(t=50, b=10, l=10, r=10),
                height=200
            ),
            use_container_width=True
        )
        
        # Memory Gauge
        st.plotly_chart(
            px.pie(
                values=[memory_usage['Memory Usage (%)'], 
                names=["Memory Usage"],
                hole=0.7,
                title=f"Memory Usage: {memory_usage['Memory Usage (%)']}%"
            ).update_traces(
                textinfo='none',
                marker=dict(colors=['#ff7f0e', '#d3d3d3'])
            ).update_layout(
                showlegend=False,
                margin=dict(t=50, b=10, l=10, r=10),
                height=200
            ),
            use_container_width=True
        )
        
    with col3:
        st.markdown("### Disk & Network")
        # Disk Usage
        st.plotly_chart(
            px.pie(
                values=[disk_usage['Disk Usage (%)'], 
                names=["Disk Usage"],
                hole=0.7,
                title=f"Disk Usage: {disk_usage['Disk Usage (%)']}%"
            ).update_traces(
                textinfo='none',
                marker=dict(colors=['#2ca02c', '#d3d3d3'])
            ).update_layout(
                showlegend=False,
                margin=dict(t=50, b=10, l=10, r=10),
                height=200
            ),
            use_container_width=True
        )
        
        # Network Info
        st.markdown(f"""
        <div class="metric-card">
            <p><b>IP Address:</b> {network_info['IP Address']}</p>
            <p><b>Data Sent:</b> {network_info['Total Data Sent (MB)']} MB</p>
            <p><b>Data Received:</b> {network_info['Total Data Received (MB)']} MB</p>
        </div>
        """, unsafe_allow_html=True)
    
    # GPU Information (if available)
    if "No GPU Detected" not in gpu_info.values():
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

# Run the app
if __name__ == "__main__":
    # Auto-refresh every 5 seconds
    st.runtime.scriptrunner.add_script_run_ctx(st.script_run_ctx)
    main()
    st.experimental_rerun()
