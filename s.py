import psutil
import platform
import os
import time
import socket
import datetime
import sys
from typing import Dict

class SystemMonitor:
    """Real-time system and power monitoring tool"""
    
    # Environmental constants
    GRID_EMISSION_FACTOR = 400  # gCO2/kWh
    BASE_PUE = 1.5  # Default PUE for standard servers

    @staticmethod
    def _enable_unicode_console():
        """Configure console for Unicode support on Windows"""
        if sys.platform == 'win32':
            try:
                # Try to configure console for UTF-8
                sys.stdout.reconfigure(encoding='utf-8')
            except:
                # Fallback for older Python versions
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    @staticmethod
    def get_all_metrics() -> Dict:
        """Collect all system metrics in one call"""
        cpu_freq = psutil.cpu_freq()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        
        return {
            "system": {
                "os": platform.system(),
                "hostname": socket.gethostname(),
                "uptime": str(datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())),
                "cores": f"{psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}"
            },
            "cpu": {
                "usage": psutil.cpu_percent(interval=1),
                "freq": cpu_freq.current if cpu_freq else None,
                "per_core": psutil.cpu_percent(interval=1, percpu=True)
            },
            "memory": {
                "total": mem.total / (1024**3),
                "used": mem.used / (1024**3),
                "percent": mem.percent
            },
            "disk": {
                "total": disk.total / (1024**3),
                "used": disk.used / (1024**3),
                "io": (disk_io.read_bytes + disk_io.write_bytes) / (1024**2)
            },
            "network": {
                "sent": net_io.bytes_sent / (1024**2),
                "recv": net_io.bytes_recv / (1024**2)
            }
        }

    @staticmethod
    def calculate_power(metrics: Dict) -> Dict:
        """Calculate power usage from metrics"""
        cpu_power = (metrics["cpu"]["usage"]/100) * (metrics["cpu"]["freq"]/1000 if metrics["cpu"]["freq"] else 2.5) * 15
        mem_power = (metrics["memory"]["used"] * 0.5) * (metrics["memory"]["percent"]/100 + 0.1)
        disk_power = 2 if metrics["disk"]["io"] > 0 else 0.5
        
        total_it_power = cpu_power + mem_power + disk_power
        total_power = total_it_power * SystemMonitor.BASE_PUE
        
        return {
            "components": {
                "cpu": round(cpu_power, 1),
                "memory": round(mem_power, 1),
                "disk": round(disk_power, 1)
            },
            "total_it": round(total_it_power, 1),
            "total_facility": round(total_power, 1),
            "pue": SystemMonitor.BASE_PUE
        }

    @staticmethod
    def calculate_emissions(power_w: float) -> Dict:
        """Calculate environmental impact"""
        hourly_co2 = (power_w/1000) * SystemMonitor.GRID_EMISSION_FACTOR
        return {
            "hourly": round(hourly_co2, 1),
            "daily": round(hourly_co2 * 24 / 1000, 2),
            "annual": round(hourly_co2 * 24 * 365 / 1000000, 3)
        }

    @staticmethod
    def display_dashboard(interval: int = 5):
        """Display real-time monitoring dashboard"""
        SystemMonitor._enable_unicode_console()
        
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                metrics = SystemMonitor.get_all_metrics()
                power = SystemMonitor.calculate_power(metrics)
                emissions = SystemMonitor.calculate_emissions(power["total_facility"])
                
                # Use ASCII-only characters for compatibility
                print("=== REAL-TIME SYSTEM MONITOR ===")
                print(f"Host: {metrics['system']['hostname']} | Uptime: {metrics['system']['uptime']}")
                print(f"CPU: {metrics['cpu']['usage']}% | Memory: {metrics['memory']['percent']}% | "
                      f"Disk: {metrics['disk']['used']:.1f}/{metrics['disk']['total']:.1f}GB")
                
                print("\n[POWER USAGE]")
                print(f"CPU: {power['components']['cpu']}W | RAM: {power['components']['memory']}W | "
                      f"Disk: {power['components']['disk']}W")
                print(f"Total IT: {power['total_it']}W | Facility: {power['total_facility']}W (PUE: {power['pue']})")
                
                print("\n[ENVIRONMENTAL IMPACT]")
                print(f"CO2: {emissions['hourly']}g/h | {emissions['daily']}kg/day | "
                      f"{emissions['annual']}t/year")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")

if __name__ == "__main__":
    SystemMonitor.display_dashboard()
