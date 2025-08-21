# 📋 Complete Radxa Rock5B+ Deployment Guide

This comprehensive guide will walk you through deploying the Radxa Rock5B+ Management System from start to finish.

## 🎯 Overview

The Radxa Rock5B+ Management System provides:
- **Access Point Management**: Switch between AP and client modes
- **Camera Streaming**: RTSP streaming with real-time monitoring
- **Network Monitoring**: Comprehensive network statistics and client management
- **Web Dashboard**: Intuitive browser-based control interface

**Estimated Time**: 15-20 minutes  
**Difficulty**: Beginner-friendly  
**Requirements**: Radxa Rock5B+, microSD card (32GB+), internet connection

## 🔧 Prerequisites

### Hardware Requirements
- **Radxa Rock5B+** board
- **MicroSD Card** (32GB+ recommended, Class 10)
- **WiFi Adapter** with AP mode support (built-in or USB)
- **USB Camera** (optional, for streaming)
- **Ethernet Cable** (for initial setup)
- **Monitor & Keyboard** (for initial setup)

### Software Requirements
- **Ubuntu 22.04 LTS** (ARM64) for Rock5B+
- **Internet Connection** (for downloading dependencies)
- **SSH Access** (optional, for remote management)

## 📀 Step 1: Prepare Radxa Rock5B+

### 1.1 Download Ubuntu Image

Download the official Ubuntu image for Rock5B+:
```bash
# Visit: https://github.com/radxa-build/rock-5b-plus/releases
# Download: ubuntu-22.04-preinstalled-server-arm64+rock-5b-plus.img.xz
```

### 1.2 Flash Image to SD Card

**Using Raspberry Pi Imager (Recommended)**:
1. Download [Raspberry Pi Imager](https://rpi.org/imager)
2. Select "Use custom image" and choose your downloaded Ubuntu image
3. Select your SD card
4. Configure SSH and user account in advanced options
5. Flash the image

**Using balenaEtcher**:
1. Download [balenaEtcher](https://www.balena.io/etcher/)
2. Select the Ubuntu image file
3. Select your SD card
4. Flash the image

### 1.3 First Boot

1. **Insert SD card** into Rock5B+
2. **Connect ethernet cable** for internet access
3. **Connect monitor and keyboard**
4. **Power on** the Rock5B+
5. **Wait for boot** (first boot takes 2-3 minutes)
6. **Login** with your configured credentials

### 1.4 Initial System Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install git (if not already installed)
sudo apt install git -y

# Check system info
uname -a
lsb_release -a

# Find IP address
ip addr show
```

## 🚀 Step 2: Install Management System

### 2.1 Clone Repository

```bash
# Clone the repository
git clone https://github.com/SMT03/new-wave-linux.git

# Navigate to directory
cd new-wave-linux

# Verify files
ls -la
```

### 2.2 Run Installation

```bash
# Make installer executable (if needed)
chmod +x install.sh

# Run the installer
./install.sh
```

**What the installer does**:
- ✅ Checks system compatibility
- ✅ Installs all required packages
- ✅ Sets up Python virtual environment
- ✅ Configures network services (hostapd, dnsmasq)
- ✅ Creates systemd services
- ✅ Sets up firewall rules
- ✅ Creates management commands
- ✅ Configures automatic startup

**Installation time**: 5-10 minutes (depending on internet speed)

### 2.3 Verify Installation

```bash
# Check if installation completed successfully
echo "Installation should show: ✨ Installation completed successfully!"

# Verify radxa command is available
which radxa
radxa --help 2>/dev/null || echo "radxa command created"
```

## ⚡ Step 3: Start and Configure System

### 3.1 Start Services

```bash
# Start the management system
radxa start

# Check system status
radxa status

# View logs (optional)
radxa logs
```

### 3.2 Access Web Dashboard

1. **Find your IP address**:
   ```bash
   ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
   ```

2. **Open web browser** on any device connected to the same network

3. **Navigate to**: `http://YOUR_RADXA_IP:5000`
   - Example: `http://192.168.1.150:5000`

4. **Verify dashboard loads** and shows system information

## 🌐 Step 4: Enable Access Point Mode

### 4.1 Enable AP Mode

```bash
# Enable Access Point mode
radxa enable-ap

# This will:
# - Configure wlan0 as access point
# - Start DHCP server (192.168.4.1/24)
# - Enable WiFi hotspot
# - Set up IP forwarding
```

### 4.2 Connect to WiFi Network

**From any WiFi device**:
1. **Search for WiFi networks**
2. **Connect to**: `Radxa_Rock5B_AP`
3. **Password**: `radxa12345`
4. **Wait for connection** (device gets IP: 192.168.4.x)

### 4.3 Access AP Dashboard

1. **Open web browser** on connected device
2. **Navigate to**: `http://192.168.4.1:5000`
3. **Verify AP dashboard** loads and shows connected clients

### 4.4 Switch Back to Client Mode (Optional)

```bash
# Disable AP mode and return to normal WiFi
radxa disable-ap

# System returns to regular network client mode
```

## 📹 Step 5: Setup Camera Streaming (Optional)

### 5.1 Connect Camera

```bash
# Connect USB camera to Rock5B+

# Check if camera is detected
ls /dev/video*

# Should show: /dev/video0 (or similar)
```

### 5.2 Test Camera

```bash
# Test camera with ffmpeg
ffmpeg -f v4l2 -i /dev/video0 -t 5 -y test.mp4

# If successful, you'll have a test.mp4 file
```

### 5.3 Start Streaming

1. **Access web dashboard**: `http://192.168.4.1:5000` (AP mode) or `http://YOUR_IP:5000`
2. **Go to Camera section**
3. **Click "Start Camera"** button
4. **RTSP stream available at**: `rtsp://192.168.4.1:8554/live`

### 5.4 View Stream

**Using VLC Media Player**:
1. Open VLC
2. Media → Open Network Stream
3. Enter: `rtsp://192.168.4.1:8554/live`
4. Click Play

## 🔧 Step 6: Management and Monitoring

### 6.1 System Management Commands

```bash
# Service control
radxa start          # Start all services
radxa stop           # Stop all services
radxa restart        # Restart all services
radxa status         # Check system status
radxa logs           # View system logs

# Network management
radxa enable-ap      # Enable Access Point mode
radxa disable-ap     # Disable Access Point mode

# Maintenance
radxa reset          # Reset to default settings
radxa uninstall      # Remove system completely
```

### 6.2 Monitor System Health

```bash
# Check service status
sudo systemctl status radxa-system

# View detailed logs
sudo journalctl -u radxa-system -f

# Check network interfaces
ip addr show

# Monitor connected clients (in AP mode)
cat /var/lib/dhcp/dhcpd.leases
```

### 6.3 Web Dashboard Features

**Navigation Sections**:
- **Dashboard**: System overview and status
- **Network**: Interface statistics and client management
- **Camera**: Live stream and recording controls
- **AP Management**: WiFi hotspot configuration
- **System**: Performance monitoring and logs

## 🔍 Troubleshooting

### Common Installation Issues

**Issue**: Package installation failures
```bash
# Solution: Update package lists and retry
sudo apt update
sudo apt install -f
./install.sh
```

**Issue**: Permission denied errors
```bash
# Solution: Ensure user has sudo privileges
sudo usermod -aG sudo $USER
# Logout and login again
```

### Network Issues

**Issue**: AP mode not working
```bash
# Check WiFi adapter supports AP mode
iw list | grep -A 10 "Supported interface modes"

# Should show "AP" in the list
```

**Issue**: Can't access web dashboard
```bash
# Check if service is running
radxa status

# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp

# Check IP address
ip addr show
```

### Camera Issues

**Issue**: Camera not detected
```bash
# Check USB devices
lsusb

# Check video devices
ls -la /dev/video*

# Check camera permissions
sudo usermod -aG video $USER
```

**Issue**: RTSP stream not working
```bash
# Check if ffmpeg is installed
ffmpeg -version

# Test camera manually
ffmpeg -f v4l2 -i /dev/video0 -t 5 test.mp4
```

### Service Issues

**Issue**: Services won't start
```bash
# Check systemd status
sudo systemctl status radxa-system

# Check logs
sudo journalctl -u radxa-system --no-pager

# Restart service
sudo systemctl restart radxa-system
```

## 📖 Advanced Configuration

### Custom WiFi Settings

Edit AP configuration:
```bash
sudo nano /etc/hostapd/hostapd.conf

# Change SSID and password:
ssid=Your_Custom_Name
wpa_passphrase=your_custom_password

# Restart AP mode
radxa disable-ap
radxa enable-ap
```

### Custom Web Port

Change web dashboard port:
```bash
sudo nano /opt/radxa/config/system.yaml

# Change:
web_port: 8080  # Instead of 5000

# Restart system
radxa restart
```

### Enable Auto-start

```bash
# Enable automatic startup on boot
sudo systemctl enable radxa-system

# Disable automatic startup
sudo systemctl disable radxa-system
```

## 🗑️ Uninstallation

To completely remove the system:

```bash
# Run uninstaller
radxa uninstall

# Or manually:
sudo /opt/radxa/scripts/uninstall.sh
```

**What gets removed**:
- All installed files and directories
- Systemd services
- Network configurations
- Python virtual environment
- Management commands
- Firewall rules

**What gets restored**:
- Original network configurations
- Default system settings

## 📞 Support

If you encounter issues:

1. **Check logs**: `radxa logs`
2. **Verify status**: `radxa status`
3. **Review troubleshooting section** above
4. **Check GitHub Issues**: [Repository Issues](https://github.com/SMT03/new-wave-linux/issues)
5. **Create new issue** with logs and system information

## 🎉 Success!

You now have a fully functional Radxa Rock5B+ Management System with:
- ✅ Web-based control dashboard
- ✅ Access Point capabilities
- ✅ Network monitoring
- ✅ Camera streaming (if configured)
- ✅ Easy management commands

**Next Steps**:
- Explore the web dashboard features
- Configure camera streaming if needed
- Set up remote access if desired
- Customize settings for your use case

---

**Happy managing! 🚀**
