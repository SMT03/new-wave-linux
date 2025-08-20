# Radxa Rock5B+ Network & Camera Management System

A comprehensive system for Radxa Rock5B+ that provides:
- AP mode switching and network management
- Live camera streaming with RTSP
- Real-time network monitoring and statistics
- CCTV footage analysis and bandwidth calculation
- Web-based dashboard for system control

## Features

- **Access Point Management**: Switch between AP mode and normal WiFi client mode
- **Camera Streaming**: Connect to cameras and stream via RTSP protocol
- **Network Monitoring**: Real-time network statistics, client info, DHCP leases
- **Bandwidth Analysis**: Calculate raw CCTV footage requirements
- **Web Dashboard**: Control panel for all system functions

## Hardware Requirements

- Radxa Rock5B+ board
- USB WiFi adapter (for AP mode)
- Camera (USB/IP camera)
- MicroSD card (32GB+ recommended)

## Installation

### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y hostapd dnsmasq dhcpcd5 iptables-persistent
sudo apt install -y ffmpeg v4l-utils gstreamer1.0-tools
sudo apt install -y python3-pip python3-venv git
sudo apt install -y iftop nethogs vnstat tcpdump wireshark
sudo apt install -y nginx supervisor
```

### Python Environment Setup

```bash
python3 -m venv radxa_env
source radxa_env/bin/activate
pip install -r requirements.txt
```

### Transfer to Radxa

```bash
# From your development machine:
scp -r /path/to/new-wave-linux radxa@<radxa-ip>:~/
ssh radxa@<radxa-ip>
cd ~/new-wave-linux
chmod +x scripts/*.sh
sudo ./scripts/install.sh
```

## Usage

### Start the System
```bash
sudo systemctl start radxa-manager
```

### Web Interface
Open browser: `http://<radxa-ip>:8080`

### Command Line Tools
```bash
# Switch to AP mode
sudo python3 src/ap_manager.py --enable-ap

# Start camera streaming
python3 src/camera_streamer.py --camera /dev/video0

# Monitor network
python3 src/network_monitor.py --interface wlan0
```

## Configuration

Edit `config/settings.yaml` for system configuration.

## Architecture

```
├── src/                    # Python source code
├── config/                 # Configuration files
├── scripts/                # Shell scripts for setup
├── web/                    # Web dashboard
├── systemd/                # Systemd service files
└── docs/                   # Documentation
```

## System Management

### Quick Reset (Development)
```bash
# Reset system to normal network mode
sudo /opt/radxa/scripts/reset.sh
```

### Complete Uninstall
```bash
# Remove all components and revert changes
sudo /opt/radxa/scripts/uninstall.sh
```

The uninstall script will:
- Stop and remove all services
- Restore original network configurations  
- Remove application files and logs
- Reset iptables rules
- Optional: Remove Python packages and user accounts