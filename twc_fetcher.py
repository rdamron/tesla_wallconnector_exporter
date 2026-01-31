#!/usr/bin/python3 -u

import argparse
import json
import os
import sys
import threading
import time
from urllib.request import urlopen
from urllib.error import URLError
from http.server import HTTPServer, BaseHTTPRequestHandler


# Metric storage
class Metric:
    def __init__(self, name, help_text, metric_type='gauge', value=0.0):
        self.name = name
        self.help = help_text
        self.metric_type = metric_type
        self.value = value
        self.labels = {}
    
    def set(self, value):
        if isinstance(value, (int, float)):
            self.value = float(value)
        elif isinstance(value, bool):
            self.value = float(1 if value else 0)
        elif isinstance(value, list):
            # For arrays, store count as value and array as label
            self.value = float(len(value))
            self.labels['values'] = ','.join(str(v) for v in value)
        elif isinstance(value, str):
            # For strings, store 1 as value and string as label
            self.value = 1.0
            self.labels['value'] = value
        else:
            self.value = 0.0
    
    def get(self):
        return self.value
    
    def format_for_prometheus(self):
        """Format metric for Prometheus output."""
        if self.labels:
            label_str = ','.join(f'{k}="{v}"' for k, v in self.labels.items())
            return f'{self.name}{{{label_str}}} {self.value}'
        else:
            return f'{self.name} {self.value}'


# Metric registry
metrics = {}

def register_metric(name, help_text, metric_type='gauge'):
    metric = Metric(name, help_text, metric_type)
    metrics[name] = metric
    return metric


# Register all metrics
contactor_closed = register_metric('contactor_closed', 'Indicates if contactor is closed')
vehicle_connected = register_metric('vehicle_connected', 'Indicates if vehicle is connected')
session_s = register_metric('session_s', 'Number of second the vehicle is currently being charged')
grid_v = register_metric('grid_v', 'Current voltage of grid')
grid_hz = register_metric('grid_hz', 'Current grid frequency')
vehicle_current_a = register_metric('vehicle_current_a', 'Current amps to vehicle')
currentA_a = register_metric('currentA_a', 'Current amps phase 1')
currentB_a = register_metric('currentB_a', 'Current amps phase 2')
currentC_a = register_metric('currentC_a', 'Current amps phase 3')
currentN_a = register_metric('currentN_a', 'Current amps neutral')
voltageA_v = register_metric('voltageA_v', 'Current voltage phase 1')
voltageB_v = register_metric('voltageB_v', 'Current voltage phase 2')
voltageC_v = register_metric('voltageC_v', 'Current voltage phase 3')
relay_coil_v = register_metric('relay_coil_v', 'Current voltage relay coil')
pcba_temp_c = register_metric('pcba_temp_c', 'Current temperature PCBA')
handle_temp_c = register_metric('handle_temp_c', 'Current temperature handle')
mcu_temp_c = register_metric('mcu_temp_c', 'Current temperature MCU')
uptime_s = register_metric('uptime_s', 'Uptime in seconds')
input_thermopile_uv = register_metric('input_thermopile_uv', 'Thermopile element uv')
prox_v = register_metric('prox_v', 'Prox voltage')
pilot_high_v = register_metric('pilot_high_v', 'Pilot high voltage')
pilot_low_v = register_metric('pilot_low_v', 'Pilot high voltage')
session_energy_wh = register_metric('session_energy_wh', 'Used energy of this charging session')
config_status = register_metric('config_status', 'Config status')
evse_state = register_metric('evse_state', 'Evse state')
current_alerts = register_metric('current_alerts', 'Current alerts (count and list)')
evse_not_ready_reasons = register_metric('evse_not_ready_reasons', 'EVSE not ready reasons (count and list)')

wifi_signal_strength = register_metric('wifi_signal_strength', 'WiFi signal strength')
wifi_rssi = register_metric('wifi_rssi', 'WiFi RSSI')
wifi_snr = register_metric('wifi_snr', 'WiFi SNR')
wifi_connected = register_metric('wifi_connected', 'WiFi connected')
internet = register_metric('internet', 'Internet connected')
wifi_ssid = register_metric('wifi_ssid', 'WiFi SSID info')
wifi_mac = register_metric('wifi_mac', 'WiFi MAC address info')
wifi_infra_ip = register_metric('wifi_infra_ip', 'WiFi IP address info')

contactor_cycles_loaded = register_metric('contactor_cycles_loaded', 'Contactor Cycles loaded')
contactor_cycles = register_metric('contactor_cycles', 'Contactor Cycles')
alert_count = register_metric('alert_count', 'Alert Count')
thermal_foldbacks = register_metric('thermal_foldbacks', 'Thermal foldbacks')
charge_starts = register_metric('charge_starts', 'Charge Starts')
energy_wh = register_metric('energy_wh', 'Alltime Charged wh')
connector_cycles = register_metric('connector_cycles', 'Connector Cycles')
uptime_all = register_metric('uptime_all', 'Uptime in seconds')
charging_time_s = register_metric('charging_time_s', 'Charging Time in seconds')


def fetch_json(url):
    """Fetch JSON data from URL using urllib."""
    try:
        with urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except URLError as e:
        print(f"ERROR: Failed to fetch {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Exception while fetching {url}: {e}", file=sys.stderr)
        return None


def update_metrics(ip_address):
    """Fetch and update all metrics from the Tesla Wall Connector."""
    # Fetch vitals
    response = fetch_json(f'http://{ip_address}/api/1/vitals')
    if response:
        contactor_closed.set(response.get('contactor_closed', 0))
        vehicle_connected.set(response.get('vehicle_connected', 0))
        session_s.set(response.get('session_s', 0))
        grid_v.set(response.get('grid_v', 0))
        grid_hz.set(response.get('grid_hz', 0))
        vehicle_current_a.set(response.get('vehicle_current_a', 0))
        currentA_a.set(response.get('currentA_a', 0))
        currentB_a.set(response.get('currentB_a', 0))
        currentC_a.set(response.get('currentC_a', 0))
        currentN_a.set(response.get('currentN_a', 0))
        voltageA_v.set(response.get('voltageA_v', 0))
        voltageB_v.set(response.get('voltageB_v', 0))
        voltageC_v.set(response.get('voltageC_v', 0))
        relay_coil_v.set(response.get('relay_coil_v', 0))
        pcba_temp_c.set(response.get('pcba_temp_c', 0))
        handle_temp_c.set(response.get('handle_temp_c', 0))
        mcu_temp_c.set(response.get('mcu_temp_c', 0))
        uptime_s.set(response.get('uptime_s', 0))
        input_thermopile_uv.set(response.get('input_thermopile_uv', 0))
        prox_v.set(response.get('prox_v', 0))
        pilot_high_v.set(response.get('pilot_high_v', 0))
        pilot_low_v.set(response.get('pilot_low_v', 0))
        session_energy_wh.set(response.get('session_energy_wh', 0))
        config_status.set(response.get('config_status', 0))
        evse_state.set(response.get('evse_state', 0))
        current_alerts.set(response.get('current_alerts', []))
        evse_not_ready_reasons.set(response.get('evse_not_ready_reasons', []))

    # Fetch wifi status
    response = fetch_json(f'http://{ip_address}/api/1/wifi_status')
    if response:
        wifi_signal_strength.set(response.get('wifi_signal_strength', 0))
        wifi_rssi.set(response.get('wifi_rssi', 0))
        wifi_snr.set(response.get('wifi_snr', 0))
        wifi_connected.set(response.get('wifi_connected', 0))
        internet.set(response.get('internet', 0))
        wifi_ssid.set(response.get('wifi_ssid', ''))
        wifi_mac.set(response.get('wifi_mac', ''))
        wifi_infra_ip.set(response.get('wifi_infra_ip', ''))

    # Fetch lifetime stats
    try:
        with urlopen(f'http://{ip_address}/api/1/lifetime', timeout=5) as resp:
            response_text = resp.read().decode('utf-8')
            # Removing avg_startup_temp due to wrong format provided by the Wallbox
            response_text = response_text.replace('"avg_startup_temp":nan,', '')
            response = json.loads(response_text)
            
            contactor_cycles_loaded.set(response.get('contactor_cycles_loaded', 0))
            contactor_cycles.set(response.get('contactor_cycles', 0))
            alert_count.set(response.get('alert_count', 0))
            thermal_foldbacks.set(response.get('thermal_foldbacks', 0))
            charge_starts.set(response.get('charge_starts', 0))
            energy_wh.set(response.get('energy_wh', 0))
            connector_cycles.set(response.get('connector_cycles', 0))
            uptime_all.set(response.get('uptime_s', 0))
            charging_time_s.set(response.get('charging_time_s', 0))
    except Exception as e:
        print(f"ERROR: Failed to fetch lifetime stats: {e}", file=sys.stderr)


def generate_prometheus_metrics():
    """Generate metrics in Prometheus text format."""
    output = []
    for metric_name, metric in metrics.items():
        output.append(f'# HELP {metric_name} {metric.help}')
        output.append(f'# TYPE {metric_name} {metric.metric_type}')
        output.append(metric.format_for_prometheus())
    return '\n'.join(output) + '\n'


# HTTP server for Prometheus scraping
class MetricsHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def do_GET(self):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        status_code = 200  # Default
        
        if self.path == '/metrics':
            status_code = 200
            self.send_response(status_code)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(generate_prometheus_metrics().encode('utf-8'))
        elif self.path == '/':
            status_code = 200
            self.send_response(status_code)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = '''<!DOCTYPE html>
<html>
<head><title>Tesla Wall Connector Exporter</title></head>
<body>
<h1>Tesla Wall Connector Exporter</h1>
<p><a href="/metrics">Metrics</a></p>
</body>
</html>'''
            self.wfile.write(html.encode('utf-8'))
        else:
            status_code = 404
            self.send_response(status_code)
            self.end_headers()
        
        print(f"[{timestamp}] {self.client_address[0]} - GET {self.path} - {status_code}")


def metric_updater(ip_address, interval):
    """Background thread to periodically update metrics."""
    while True:
        try:
            update_metrics(ip_address)
        except Exception as e:
            print(f"ERROR in metric updater: {e}", file=sys.stderr)
        time.sleep(interval)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Tesla Wall Connector Prometheus Exporter',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        'wallconnector',
        nargs='?',
        default=os.environ.get('TWC_ADDRESS', 'twc.local'),
        help='Tesla Wall Connector hostname or IP address (env: TWC_ADDRESS)'
    )

    parser.add_argument(
        '-p', '--port',
        type=int,
        default=int(os.environ.get('TWC_PORT', '56852')),
        help='HTTP server port for metrics endpoint (env: TWC_PORT)'
    )

    parser.add_argument(
        '-i', '--interval',
        type=int,
        default=int(os.environ.get('TWC_INTERVAL', '10')),
        help='Update interval in seconds (env: TWC_INTERVAL)'
    )

    parser.add_argument(
        '-b', '--bind',
        default=os.environ.get('TWC_BIND', ''),
        help='Bind address for HTTP server (default: all interfaces, env: TWC_BIND)'
    )
    
    args = parser.parse_args()
    
    ip_address = args.wallconnector
    server_port = args.port
    update_interval = args.interval
    bind_address = args.bind
    
    print("Tesla Wall Connector Exporter")
    print("=" * 50)
    print(f"Wall Connector: {ip_address}")
    print(f"Server Address: {bind_address if bind_address else '0.0.0.0'}:{server_port}")
    print(f"Update Every:   {update_interval} seconds")
    print("=" * 50)
    print()
    
    # Initial metric fetch
    print("Fetching initial metrics...")
    update_metrics(ip_address)
    print("Done!")
    print()
    
    # Start background updater thread
    updater_thread = threading.Thread(
        target=metric_updater,
        args=(ip_address, update_interval),
        daemon=True
    )
    updater_thread.start()
    
    # Start HTTP server
    print(f"Starting HTTP server...")
    print(f"Metrics available at: http://{bind_address if bind_address else '0.0.0.0'}:{server_port}/metrics")
    print()
    
    server = HTTPServer((bind_address, server_port), MetricsHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
