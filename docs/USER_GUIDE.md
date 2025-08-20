# Radxa Rock5B+ Complete User Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage Guide](#usage-guide)
6. [Web Dashboard](#web-dashboard)
7. [Command Line Tools](#command-line-tools)
8. [Bandwidth Calculations](#bandwidth-calculations)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

## Overview

The Radxa Rock5B+ Network & Camera Management System provides:

- **Access Point Management**: Switch between AP mode and WiFi client mode
- **Camera Streaming**: USB/IP camera support with RTSP streaming
- **Network Monitoring**: Real-time bandwidth, statistics, and diagnostics
- **Web Dashboard**: Complete control interface accessible via browser
- **Bandwidth Analysis**: Calculate raw CCTV footage requirements

## Hardware Requirements

### Minimum Requirements
- Radxa Rock5B+ single board computer
- MicroSD card (32GB+ recommended)
- Power supply (5V/4A recommended)
- Network connection (Ethernet or WiFi)

### Optional Hardware
- USB WiFi adapter (for AP mode while maintaining ethernet connection)
- USB camera or IP camera
- External storage for video recording

### Supported Cameras
- USB UVC (Video Class) cameras
- V4L2 compatible devices
- IP cameras (RTSP/HTTP streams)
- Common resolutions: 720p, 1080p, 4K

## Installation

### Method 1: Remote Installation via SSH

1. **Prepare your development machine:**
   ```bash
   git clone <your-repo-url>
   cd new-wave-linux
   chmod +x scripts/deploy.sh
   ```

2. **Transfer and install to Radxa:**
   ```bash
   # Basic transfer
   ./scripts/deploy.sh 192.168.1.100

   # Transfer and install
   ./scripts/deploy.sh 192.168.1.100 --install

   # Transfer, install, and start services
   ./scripts/deploy.sh 192.168.1.100 --install --start

   # Using SSH key
   ./scripts/deploy.sh 192.168.1.100 -k ~/.ssh/radxa_key --install --start
   ```

### Method 2: Direct Installation on Radxa

1. **Copy files to Radxa:**
   ```bash
   scp -r new-wave-linux radxa@<radxa-ip>:~/
   ```

2. **SSH to Radxa and install:**
   ```bash
   ssh radxa@<radxa-ip>
   cd ~/new-wave-linux
   chmod +x scripts/install.sh
   sudo ./scripts/install.sh
   ```

### Installation Components

The installer sets up:
- Python virtual environment (`/opt/radxa/venv`)
- System services (`radxa-manager`, `radxa-network-monitor`)
- Configuration files (`/etc/radxa/settings.yaml`)
- Command line tools (`radxa-*` commands)
- Web server (nginx reverse proxy)
- Log rotation and system permissions

## Configuration

### Main Configuration File
Edit `/etc/radxa/settings.yaml` to customize settings:

```yaml
# Network Configuration
network:
  wifi_interface: "wlan0"
  ethernet_interface: "eth0"
  ap_config:
    ssid: "RadxaAP"
    password: "radxa2024"
    channel: 7
    ip_range: "192.168.4.0/24"

# Camera Configuration
camera:
  default_device: "/dev/video0"
  rtsp:
    port: 8554
    path: "/live"
  video:
    width: 1920
    height: 1080
    fps: 30
    bitrate: "2M"
```

### Service Management
```bash
# Start all services
sudo radxa-start

# Stop all services
sudo radxa-stop

# Check service status
radxa-status

# Individual service control
sudo systemctl start/stop/restart radxa-manager
sudo systemctl start/stop/restart radxa-network-monitor
```

## Usage Guide

### Access Point Mode

**Enable AP Mode:**
```bash
# Command line
sudo radxa-ap --enable-ap

# Or via web dashboard
# Go to http://<radxa-ip>:8080
# Click "Enable AP" in Access Point section
```

**Features:**
- Creates WiFi hotspot with configurable SSID/password
- DHCP server for client IP assignment
- NAT routing to ethernet connection
- Client monitoring and statistics

**Disable AP Mode:**
```bash
sudo radxa-ap --disable-ap
```

### Camera Streaming

**List Available Cameras:**
```bash
radxa-camera --list-cameras
```

**Start Camera Streaming:**
```bash
# Start basic streaming
radxa-camera --camera /dev/video0 --stream

# Start RTSP server
radxa-camera --camera /dev/video0 --start-rtsp

# Performance test
radxa-camera --camera /dev/video0 --test 30
```

**RTSP Stream Access:**
- URL: `rtsp://<radxa-ip>:8554/live`
- Compatible with VLC, FFmpeg, and most IP camera software

### Network Monitoring

**Real-time Monitoring:**
```bash
# Monitor specific interface
radxa-network --interface wlan0 --continuous

# Monitor all interfaces for 60 seconds
radxa-network --duration 60

# Export monitoring data
radxa-network --export network_data.json
```

**Monitoring Features:**
- Real-time bandwidth utilization
- Interface statistics (packets, errors, drops)
- System performance metrics
- DHCP lease information
- DNS server configuration
- Routing table analysis

## Web Dashboard

Access the web interface at `http://<radxa-ip>:8080`

### Dashboard Sections

**1. Status Bar**
- Access Point status indicator
- Camera connection status  
- Real-time monitoring status
- Last update timestamp

**2. Access Point Control**
- Enable/disable AP mode
- View connected clients
- SSID and network configuration

**3. Network Statistics**
- Real-time bandwidth graphs
- Data transfer statistics
- Network interface information
- Speed measurements

**4. Camera Streaming**
- Camera device selection
- Start/stop streaming controls
- RTSP server management
- Frame rate and quality metrics

**5. System Performance**
- CPU, memory, and disk usage
- Load average monitoring
- Performance history graphs

**6. Real-time Logs**
- System event logging
- Error messages and status updates
- Filterable log output

### WebSocket Features
- Real-time data updates every 2 seconds
- Interactive charts and graphs
- Live status indicators
- Instant command feedback

## Command Line Tools

### radxa-ap (Access Point Management)
```bash
# Enable AP mode
sudo radxa-ap --enable-ap

# Disable AP mode  
sudo radxa-ap --disable-ap

# Show current status
radxa-ap --status

# Use custom config file
radxa-ap --config /path/to/settings.yaml --enable-ap
```

### radxa-camera (Camera Control)
```bash
# List available cameras
radxa-camera --list-cameras

# Start streaming with display
radxa-camera --camera /dev/video0 --stream

# Start RTSP server
radxa-camera --start-rtsp --port 8554

# Performance test
radxa-camera --test 30 --camera /dev/video0

# Show statistics
radxa-camera --stats --camera /dev/video0
```

### radxa-network (Network Monitoring)
```bash
# Show current status
radxa-network --status

# Monitor specific interface
radxa-network --interface eth0 --duration 60

# Continuous monitoring
radxa-network --continuous

# Export data
radxa-network --export data.json --duration 120
```

## Bandwidth Calculations

### Using the Bandwidth Calculator

```bash
# Calculate for 1080p at 30fps
python3 /opt/radxa/bandwidth_calculator.py --resolution 1080p --fps 30

# Calculate with compression
python3 /opt/radxa/bandwidth_calculator.py --width 1920 --height 1080 --fps 30 --compression h264_medium

# List available options
python3 /opt/radxa/bandwidth_calculator.py --list-resolutions
python3 /opt/radxa/bandwidth_calculator.py --list-compressions

# Multiple stream calculation
python3 /opt/radxa/bandwidth_calculator.py --config-file streams.yaml
```

### Example Stream Configuration (streams.yaml)
```yaml
streams:
  - name: "Main Camera"
    width: 1920
    height: 1080
    fps: 30
    compression: "h264_medium"
  - name: "Secondary Camera"
    width: 1280
    height: 720
    fps: 15
    compression: "h264_high"
```

### Bandwidth Requirements Examples

| Resolution | FPS | Raw Bandwidth | H.264 Medium | H.265 High |
|------------|-----|---------------|--------------|------------|
| 720p       | 30  | 665 Mbps      | 10 Mbps      | 3.3 Mbps   |
| 1080p      | 30  | 1.49 Gbps     | 22 Mbps      | 7.5 Mbps   |
| 4K         | 30  | 5.97 Gbps     | 89 Mbps      | 30 Mbps    |

## Troubleshooting

### Common Issues

**1. SSH Connection Failed**
```bash
# Check SSH service
sudo systemctl status ssh

# Check network connectivity
ping <radxa-ip>

# Verify SSH key permissions
chmod 600 ~/.ssh/your_key
```

**2. Camera Not Detected**
```bash
# Check video devices
ls -la /dev/video*

# Check USB devices
lsusb

# Test camera access
v4l2-ctl --list-devices

# Check permissions
sudo usermod -a -G video $USER
```

**3. Access Point Not Working**
```bash
# Check hostapd status
sudo systemctl status hostapd

# Check interface status
ip addr show wlan0

# Check dnsmasq status
sudo systemctl status dnsmasq

# View logs
sudo journalctl -u hostapd -f
```

**4. Web Dashboard Not Accessible**
```bash
# Check service status
sudo systemctl status radxa-manager

# Check port binding
sudo netstat -tlnp | grep 8080

# Check firewall
sudo ufw status

# View application logs
sudo journalctl -u radxa-manager -f
```

**5. Network Monitoring Issues**
```bash
# Check interface names
ip link show

# Verify permissions
sudo usermod -a -G netdev $USER

# Check system resources
top
free -h
df -h
```

### Log Locations
- System logs: `/var/log/radxa/`
- Service logs: `sudo journalctl -u radxa-manager`
- Network logs: `sudo journalctl -u radxa-network-monitor`
- Nginx logs: `/var/log/nginx/`

### Performance Optimization

**1. For High Bandwidth Streaming:**
```bash
# Increase network buffers
echo 'net.core.rmem_max = 268435456' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 268435456' | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

**2. For Multiple Cameras:**
```bash
# Increase USB buffer size
echo 'usbcore.usbfs_memory_mb=1000' | sudo tee -a /etc/default/grub
sudo update-grub
```

**3. For Better WiFi Performance:**
```bash
# Set WiFi power management off
sudo iwconfig wlan0 power off

# Set channel width
sudo iw dev wlan0 set channel 36 HT40+
```

## API Reference

### REST API Endpoints

**System Status**
```
GET /api/status
```
Returns complete system status including AP, camera, and network information.

**Access Point Control**
```
POST /api/ap/enable
POST /api/ap/disable
```

**Camera Control**
```
GET /api/cameras
POST /api/camera/start
POST /api/camera/stop
POST /api/camera/rtsp/start
POST /api/camera/rtsp/stop
```

**Network Information**
```
GET /api/network/interfaces
GET /api/network/bandwidth/<interface>?duration=60
```

**Configuration**
```
GET /api/config
POST /api/config
```

### WebSocket Events

**Client to Server:**
- `start_monitoring` - Start real-time monitoring
- `stop_monitoring` - Stop real-time monitoring

**Server to Client:**
- `real_time_data` - Real-time system data
- `monitoring_status` - Monitoring state changes
- `status` - Connection status messages

### Example API Usage

```python
import requests

# Get system status
response = requests.get('http://radxa-ip:8080/api/status')
status = response.json()

# Enable AP mode
requests.post('http://radxa-ip:8080/api/ap/enable')

# Start camera
requests.post('http://radxa-ip:8080/api/camera/start', 
              json={'device': '/dev/video0'})
```

## Advanced Configuration

### Custom Video Encoding
Edit `/etc/radxa/settings.yaml`:
```yaml
camera:
  video:
    codec: "h264"
    bitrate: "2M"
    quality: "medium"
    keyframe_interval: 30
```

### Network Interface Priorities
```yaml
monitoring:
  interfaces:
    - "eth0"    # Highest priority
    - "wlan0"   # Second priority
    - "wlan1"   # Lowest priority
```

### Performance Tuning
```yaml
performance:
  max_streams: 4
  network_buffer_size: 65536
  video_buffer_size: 1048576
  max_cpu_percent: 80
```

This completes the comprehensive user guide for the Radxa Rock5B+ Network & Camera Management System. The system provides enterprise-grade functionality with an easy-to-use interface for both web and command-line management.
