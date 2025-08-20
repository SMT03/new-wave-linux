# 🚀 Quick Start Guide

## Transfer to Radxa Rock5B+

### Method 1: Automated Transfer + Installation

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Transfer, install, and start (replace with your Radxa IP)
./scripts/deploy.sh 192.168.1.100 --install --start
```

### Method 2: Manual Transfer

```bash
# Transfer files
scp -r new-wave-linux radxa@192.168.1.100:~/

# SSH to Radxa
ssh radxa@192.168.1.100

# Install
cd new-wave-linux
sudo ./scripts/install.sh
```

## First Time Setup

1. **Access Web Dashboard**: `http://192.168.1.100:8080`
2. **Enable AP Mode**: Click "Enable AP" in dashboard
3. **Connect Camera**: Plug in USB camera and click "Start Camera"
4. **Start RTSP**: Click "Start RTSP" for streaming
5. **Monitor Network**: Click "Start Monitoring" for real-time stats

## Quick Commands

```bash
# Service management
sudo radxa-start          # Start all services
sudo radxa-stop           # Stop all services
radxa-status             # Check status

# Access Point
sudo radxa-ap --enable-ap    # Enable AP mode
sudo radxa-ap --disable-ap   # Disable AP mode

# Camera
radxa-camera --list-cameras  # List cameras
radxa-camera --start-rtsp    # Start RTSP server

# Network monitoring
radxa-network --status       # Show network status
```

## URLs

- **Web Dashboard**: `http://<radxa-ip>:8080`
- **RTSP Stream**: `rtsp://<radxa-ip>:8554/live`

## Default Settings

- **AP SSID**: RadxaAP
- **AP Password**: radxa2024
- **RTSP Port**: 8554
- **Web Port**: 8080

That's it! Your Radxa Rock5B+ is now a powerful network and camera management system! 🎉
