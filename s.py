import psutil
import platform
import shutil
import socket
import getpass
import datetime
import uuid
import GPUtil  # For GPU Info (Install using: pip install GPUtil)

# Constants for calculations
GRID_EMISSION_FACTOR = 400  # gCO2/kWh (US average)
WATER_USAGE_IMPACT = 0.001  # Placeholder - adjust based on actual water usage

def get_system_info():
    """Fetches system-level details."""
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
    """Fetches CPU usage details."""
    return {
        "CPU Usage (%)": psutil.cpu_percent(interval=1),
        "CPU Frequency (MHz)": psutil.cpu_freq().current if psutil.cpu_freq() else "N/A"
    }

def get_memory_usage():
    """Fetches Memory usage details."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "Memory Usage (%)": mem.percent,
        "Total Memory (GB)": round(mem.total / (1024 ** 3), 2),
        "Used Memory (GB)": round(mem.used / (1024 ** 3), 2),
        "Swap Usage (%)": swap.percent
    }

def get_disk_usage():
    """Fetches Disk usage details."""
    disk = shutil.disk_usage("/")
    return {
        "Total Disk Space (GB)": round(disk.total / (1024 ** 3), 2),
        "Used Disk Space (GB)": round(disk.used / (1024 ** 3), 2),
        "Free Disk Space (GB)": round(disk.free / (1024 ** 3), 2),
        "Disk Usage (%)": round((disk.used / disk.total) * 100, 2)
    }

def get_network_info():
    """Fetches Network details."""
    net_io = psutil.net_io_counters()
    return {
        "IP Address": socket.gethostbyname(socket.gethostname()),
        "Total Data Sent (MB)": round(net_io.bytes_sent / (1024 ** 2), 2),
        "Total Data Received (MB)": round(net_io.bytes_recv / (1024 ** 2), 2)
    }

def get_gpu_info():
    """Fetches GPU details (if available)."""
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

def get_system_boot_time():
    """Fetches system boot time."""
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    return {"Last Boot Time": boot_time.strftime("%Y-%m-%d %H:%M:%S")}

def calculate_energy_metrics():
    """Calculates PUE, SUE, and Carbon Intensity metrics."""
    # These would normally come from actual power monitoring hardware
    # For demonstration, we'll use some example values
    it_equipment_power = 60.51  # Watts (IT load)
    total_facility_power = 93.79  # Watts (total power)
    cooling_overhead = total_facility_power - it_equipment_power
    
    # Calculate PUE
    if it_equipment_power > 0:
        pue = total_facility_power / it_equipment_power
    else:
        pue = 0
    
    # Calculate SUE (simplified example)
    sue = (total_facility_power + WATER_USAGE_IMPACT) / it_equipment_power if it_equipment_power > 0 else 0
    
    # Calculate Carbon Intensity
    carbon_intensity_hourly = (it_equipment_power / 1000) * GRID_EMISSION_FACTOR  # gCO2/hour
    carbon_intensity_annual = carbon_intensity_hourly * 24 * 365  # gCO2/year
    
    return {
        "IT Equipment Power (W)": it_equipment_power,
        "Total Facility Power (W)": total_facility_power,
        "Cooling & Overhead Power (W)": cooling_overhead,
        "Power Usage Effectiveness (PUE)": round(pue, 2),
        "Sustainable Use Effectiveness (SUE)": round(sue, 2),
        "Carbon Intensity (gCO2/hour)": round(carbon_intensity_hourly, 2),
        "Estimated Annual CO2 Emissions (kgCO2/year)": round(carbon_intensity_annual / 1000, 2)
    }

def get_complete_system_report():
    """Fetches all system information and prints it."""
    system_data = {
        **get_system_info(),
        **get_cpu_usage(),
        **get_memory_usage(),
        **get_disk_usage(),
        **get_network_info(),
        **get_gpu_info(),
        **get_system_boot_time(),
        **calculate_energy_metrics()
    }

    print("\n=== System Information Report ===\n")
    for key, value in system_data.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    get_complete_system_report()
