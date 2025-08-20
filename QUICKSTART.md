# 🚀 Radxa Rock5B+ Management System - Quick Start

## ⚡ One-Command Installation

Clone and install directly on your Radxa Rock5B+:

```bash
# 1. Clone the repository
git clone https://github.com/SMT03/new-wave-linux.git

# 2. Navigate to directory
cd new-wave-linux

# 3. Run installation
./install.sh

# 4. Start the system
radxa start
```

**That's it!** The system is now running.

## 🎯 Quick Start After Installation

```bash
# Access web dashboard
# Open browser: http://YOUR_RADXA_IP:5000

# Enable AP mode
radxa enable-ap

# Connect to WiFi: "Radxa_Rock5B_AP" (password: radxa12345)
# Access AP dashboard: http://192.168.4.1:5000
```

## 🔧 Management Commands

```bash
radxa start          # Start system
radxa stop           # Stop system
radxa restart        # Restart system
radxa status         # Check status
radxa logs           # View logs
radxa enable-ap      # Enable AP mode
radxa disable-ap     # Disable AP mode
radxa uninstall      # Remove system
radxa reset          # Reset to defaults
```

## ✨ What Gets Installed

The installer automatically sets up:
- ✅ **Python Environment**: Virtual environment with all dependencies
- ✅ **Network Services**: hostapd, dnsmasq, iptables configuration
- ✅ **Web Dashboard**: Flask-based management interface on port 5000
- ✅ **RTSP Server**: Camera streaming on port 8554
- ✅ **System Services**: Automatic startup and management
- ✅ **Management Commands**: Easy-to-use CLI tools

## 🌐 Access Points

- **Normal Mode**: `http://YOUR_RADXA_IP:5000`
- **AP Mode**: `http://192.168.4.1:5000`
- **RTSP Stream**: `rtsp://YOUR_RADXA_IP:8554/live`

## 📋 System Requirements

- Radxa Rock5B+ with Ubuntu 20.04+
- WiFi adapter with AP mode support
- Internet connection for installation
- Optional: USB camera for streaming

## 🔍 Quick Troubleshooting

**Installation Issues**:
```bash
# Check logs during installation
./install.sh 2>&1 | tee install.log

# If packages fail, update and retry
sudo apt update
./install.sh
```

**Service Issues**:
```bash
# Check system status
radxa status

# View logs
radxa logs

# Restart if needed
radxa restart
```

**Network Issues**:
```bash
# Check IP address
ip addr show

# Test AP mode support
iw list | grep -A 10 "Supported interface modes"
```

## 📖 Need More Details?

- **[Complete Deployment Guide](DEPLOYMENT_GUIDE.md)** - Step-by-step installation with troubleshooting
- **[User Guide](docs/USER_GUIDE.md)** - Complete feature documentation
- **[GitHub Repository](https://github.com/SMT03/new-wave-linux)** - Source code and issues

---

**⚡ Get started in under 10 minutes!**
