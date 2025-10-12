# Tesla Wall Connector Prometheus Exporter

A lightweight, zero-dependency Prometheus exporter for Tesla Wall Connector Gen 3. Written in pure Python using only standard library modules.

A lot of this was inspired by the many available alternatives:

- https://github.com/benclapp/tesla_wall_connector_exporter
- https://github.com/fynnsh/teslawallconnector-exporter
- https://github.com/marcsowen/teslawallconnector-exporter
- https://github.com/realdadfish/teslawallconnector

I wanted something with no external dependencies that could be easily run anywhere Python3 is available, so I asked Copilot to help me out with this.  
It also includes a couple additional features like access logging and better handling of array and string fields.  
The architecture is setup for a push model, where vector scrapes the script's `/metrics` endpoint and forwards the metrics to Prometheus (via Prometheus Remote Write) or another system. It also supports direct scraping by Prometheus.
The Grafana Dashboard is not included here, but you can find one in the other repos mentioned above.

## Features

✅ **Zero External Dependencies** - Uses only Python standard library  
✅ **Prometheus Compatible** - Standard `/metrics` endpoint  
✅ **Complete Coverage** - All 44 metrics from all API endpoints  
✅ **Smart Type Handling** - Arrays and strings exported as labeled metrics  
✅ **Auto-refresh** - Background thread updates metrics at configurable intervals  
✅ **Access Logging** - Logs all HTTP requests with timestamps and status codes  
✅ **Easy Configuration** - Command-line arguments with sensible defaults

## Requirements

- Python 3.6 or higher
- Network access to Tesla Wall Connector
- That's it! No pip packages needed.

## Collected Metrics

**Total: 44 metrics** covering all data from the Tesla Wall Connector API.

### Charging Status

- `contactor_closed` - Contactor state (0/1)
- `vehicle_connected` - Vehicle connection state (0/1)
- `session_s` - Current charging session duration (seconds)
- `session_energy_wh` - Energy delivered in current session (Wh)
- `evse_state` - EVSE state code
- `config_status` - Configuration status
- `current_alerts{values="..."}` - Current alerts (count and comma-separated list)
- `evse_not_ready_reasons{values="..."}` - EVSE not ready reasons (count and list)

### Electrical Measurements

- `grid_v` - Grid voltage (V)
- `grid_hz` - Grid frequency (Hz)
- `vehicle_current_a` - Current delivered to vehicle (A)
- `currentA_a`, `currentB_a`, `currentC_a` - Per-phase current (A)
- `currentN_a` - Neutral current (A)
- `voltageA_v`, `voltageB_v`, `voltageC_v` - Per-phase voltage (V)
- `relay_coil_v` - Relay coil voltage (V)
- `pilot_high_v`, `pilot_low_v` - Pilot signal voltages (V)
- `prox_v` - Proximity voltage (V)

### Temperature Sensors

- `pcba_temp_c` - PCBA temperature (°C)
- `handle_temp_c` - Handle temperature (°C)
- `mcu_temp_c` - MCU temperature (°C)
- `input_thermopile_uv` - Thermopile reading (µV)

### WiFi Status

- `wifi_signal_strength` - WiFi signal strength (%)
- `wifi_rssi` - WiFi RSSI (dBm)
- `wifi_snr` - WiFi signal-to-noise ratio (dB)
- `wifi_connected` - WiFi connection state (0/1)
- `internet` - Internet connectivity state (0/1)
- `wifi_ssid{value="..."}` - WiFi SSID (as label)
- `wifi_mac{value="..."}` - WiFi MAC address (as label)
- `wifi_infra_ip{value="..."}` - WiFi IP address (as label)

### Lifetime Statistics

- `energy_wh` - Total energy delivered (Wh)
- `charge_starts` - Total number of charging sessions
- `charging_time_s` - Total charging time (seconds)
- `contactor_cycles_loaded` - Contactor cycle count (loaded)
- `contactor_cycles` - Contactor cycle count (total)
- `connector_cycles` - Connector insertion count
- `alert_count` - Alert count
- `thermal_foldbacks` - Thermal foldback events
- `uptime_s` - Current uptime (seconds)
- `uptime_all` - Total uptime (seconds)

### Metric Label Format

**Arrays** (like alerts) are exported as:

```
current_alerts{values="1,2,3"} 3.0
```

Where the value is the count and the label contains comma-separated items.

**Strings** (like WiFi SSID) are exported as:

```
wifi_ssid{value="MyNetwork"} 1.0
```

Where the label contains the string value (info metric pattern).

## Installation

```bash
# Clone or download the script
git clone <repository-url>
cd tesla_wallconnector_exporter

# Make executable (optional)
chmod +x twc_fetcher.py
```

## Usage

### Basic Usage

```bash
# Use defaults (twc.local:56852, update every 10s)
python3 twc_fetcher.py

# Specify Wall Connector hostname/IP
python3 twc_fetcher.py 192.168.1.100

# With custom port
python3 twc_fetcher.py -p 9225

# With custom update interval (30 seconds)
python3 twc_fetcher.py -i 30

# Bind to specific interface
python3 twc_fetcher.py -b 127.0.0.1

# All options combined
python3 twc_fetcher.py 192.168.1.100 -p 9225 -i 15 -b 0.0.0.0
```

### Command-Line Arguments

```
usage: twc_fetcher.py [-h] [-p PORT] [-i INTERVAL] [-b BIND] [wallconnector]

positional arguments:
  wallconnector         Tesla Wall Connector hostname or IP address
                        (default: twc.local)

options:
  -h, --help            show this help message and exit
  -p, --port PORT       HTTP server port for metrics endpoint (default: 56852)
  -i, --interval INTERVAL
                        Update interval in seconds (default: 10)
  -b, --bind BIND       Bind address for HTTP server (default: all interfaces)
```

## Integration with Vector

See the included [`vector.yaml`](vector.yaml) configuration file for a complete example.

The configuration uses `prometheus_scrape` source to collect metrics from the exporter and forwards them via Prometheus Remote Write:

- Scrapes `http://localhost:56852/metrics` every 15 seconds
- Adds custom labels (origin, instance) via VRL transform
- Forwards to Prometheus using `prometheus_remote_write` sink

Update the endpoint, credentials, and labels as needed for your environment.

## Integration with Prometheus

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "tesla_wallconnector"
    static_configs:
      - targets: ["localhost:56852"]
```

## Running as a Service

### systemd Service

See the included [`twc-exporter.service`](twc-exporter.service) file for a complete systemd service definition.

To install:

```bash
# Copy files to system locations
sudo cp twc_fetcher.py /opt/
sudo cp twc-exporter.service /etc/systemd/system/

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable twc-exporter.service
sudo systemctl start twc-exporter.service

# Check status
sudo systemctl status twc-exporter.service
```

## Access Logs

The exporter logs all HTTP requests to stdout:

```
[2025-10-11 21:45:30] 127.0.0.1 - GET /metrics - 200
[2025-10-11 21:45:45] 192.168.1.100 - GET / - 200
[2025-10-11 21:46:00] 10.0.0.5 - GET /favicon.ico - 404
```

## API Endpoints

- `GET /` - Simple HTML page with link to metrics
- `GET /metrics` - Prometheus-formatted metrics

## Troubleshooting

### Connection Issues

If the exporter can't reach the Wall Connector:

```bash
# Test connectivity
ping twc.local

# Test API directly
curl http://twc.local/api/1/vitals
```

### Port Already in Use

If port 56852 is already in use:

```bash
# Use a different port
python3 twc_fetcher.py -p 9225
```

### Metrics Not Updating

Check the console output for error messages. The exporter will show:

- Initial metric fetch status
- Any errors fetching from the Wall Connector
- HTTP access logs showing scrape requests

## API Coverage

This exporter collects **all available metrics** from the Tesla Wall Connector API:

- ✅ **27/27 fields** from `/api/1/vitals`
- ✅ **8/8 fields** from `/api/1/wifi_status`
- ✅ **9/9 fields** from `/api/1/lifetime`

### Special Handling

**Arrays:** Converted to metrics with count as value and comma-separated list as label  
**Strings:** Exported as info-style metrics (value=1.0 with string in label)  
**Invalid JSON:** Automatically handles `avg_startup_temp:nan` issue

## Known Issues

The Tesla Wall Connector API sometimes returns invalid JSON with `"avg_startup_temp":nan`. This exporter automatically handles this by removing the problematic field before parsing.

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions welcome! This project aims to remain dependency-free using only Python standard library.

## Credits

Created for monitoring Tesla Wall Connector Gen 3 installations.
