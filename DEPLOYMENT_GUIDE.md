# 🚀 Radxa Rock5B+ Deployment Guide

Complete step-by-step guide to deploy your network management system.

## 📋 Prerequisites

### What You Need:
- ✅ Radxa Rock5B+ with Ubuntu/Debian installed
- ✅ MicroSD card (32GB+ recommended)
- ✅ WiFi adapter or built-in WiFi
- ✅ Ethernet connection for initial setup
- ✅ Your computer with SSH access
- ✅ Optional: USB camera or IP camera

### Network Setup:
- Radxa connected to your router via Ethernet
- Computer on the same network
- SSH enabled on Radxa

---

## 🔧 Step 1: Prepare Your Radxa

### 1.1 Flash OS (if needed)
```bash
# Download Ubuntu 24.04 for Rock5B+
# Flash to microSD using Raspberry Pi Imager or balenaEtcher
```

### 1.2 Enable SSH
```bash
# On Radxa terminal:
sudo systemctl enable ssh
sudo systemctl start ssh

# Set a password if needed:
sudo passwd rock  # or your username
```

### 1.3 Find Radxa IP Address
```bash
# On Radxa:
ip addr show

# Or from your computer:
nmap -sn 192.168.1.0/24  # Adjust network range
# Look for Rock5B+ device
```

### 1.4 Test SSH Connection
```bash
# From your computer:
ssh rock@<radxa-ip>
# Example: ssh rock@192.168.1.150

# If connection works, you're ready!
```

---

## 📦 Step 2: Deploy the System

### 2.1 Clone the Repository
```bash
# On your computer:
git clone https://github.com/SMT03/new-wave-linux.git
cd new-wave-linux
```

### 2.2 Make Scripts Executable
```bash
chmod +x scripts/*.sh
```

### 2.3 Deploy to Radxa
```bash
# Basic deployment:
./scripts/deploy.sh <radxa-ip>

# Example:
./scripts/deploy.sh 192.168.1.150

# With automatic installation:
./scripts/deploy.sh 192.168.1.150 --install

# With installation and auto-start:
./scripts/deploy.sh 192.168.1.150 --install --start
```

### 2.4 What the Deploy Script Does:
- 📁 Transfers all files to `/opt/radxa/`
- 🔧 Installs system dependencies
- 🐍 Sets up Python environment
- ⚙️ Configures systemd services
- 🌐 Sets up network configurations
- 🚀 Optionally starts services

---

## ⚙️ Step 3: Manual Installation (Alternative)

If you prefer manual control:

### 3.1 Transfer Files Only
```bash
./scripts/deploy.sh <radxa-ip>  # No flags = transfer only
```

### 3.2 SSH to Radxa and Install
```bash
ssh rock@<radxa-ip>

# Navigate to the system
cd /opt/radxa

# Run installation
sudo ./scripts/install.sh

# Start services
sudo systemctl start radxa-manager
sudo systemctl start radxa-network-monitor
```

---

## 🎯 Step 4: Verify Installation

### 4.1 Check Service Status
```bash
# On Radxa:
sudo systemctl status radxa-manager
sudo systemctl status radxa-network-monitor

# Should show "active (running)"
```

### 4.2 Check Web Dashboard
```bash
# Open browser and navigate to:
http://<radxa-ip>:5000

# Example: http://192.168.1.150:5000
```

### 4.3 Check System Logs
```bash
# View logs:
sudo journalctl -u radxa-manager -f
sudo journalctl -u radxa-network-monitor -f
```

---

## 📡 Step 5: Configure Access Point

### 5.1 Edit Configuration (Optional)
```bash
# On Radxa:
sudo nano /etc/radxa/settings.yaml

# Customize:
# - AP SSID name
# - WiFi password  
# - IP ranges
# - Camera settings
```

### 5.2 Switch to AP Mode
```bash
# Via web dashboard:
# Navigate to http://<radxa-ip>:5000
# Click "Enable AP Mode"

# Or via command line:
sudo python3 /opt/radxa/src/ap_manager.py --enable-ap
```

### 5.3 Verify AP Mode
```bash
# Check if AP is running:
sudo systemctl status hostapd
sudo systemctl status dnsmasq

# Check interface:
ip addr show wlan0
# Should show 192.168.4.1 (or your configured IP)
```

---

## 📹 Step 6: Setup Camera Streaming

### 6.1 Connect Camera
```bash
# USB Camera:
# Plug in USB camera, check:
ls /dev/video*

# IP Camera:
# Note the RTSP URL (e.g., rtsp://camera-ip:554/stream)
```

### 6.2 Configure Camera in Dashboard
```bash
# Open web dashboard: http://<radxa-ip>:5000
# Go to "Camera Settings"
# Add camera source:
# - USB: /dev/video0
# - IP Camera: rtsp://camera-ip:554/stream
```

### 6.3 Start Streaming
```bash
# Via dashboard: Click "Start Streaming"

# Or command line:
python3 /opt/radxa/src/camera_streamer.py --camera /dev/video0
```

---

## 📱 Step 7: Connect Devices

### 7.1 Find the Access Point
```bash
# On your phone/laptop WiFi settings:
# Look for: "Radxa_Rock5B_AP" (or your custom SSID)
```

### 7.2 Connect to AP
```bash
# Default credentials:
# SSID: Radxa_Rock5B_AP  
# Password: radxa12345

# Or check your custom settings in:
# /etc/radxa/settings.yaml
```

### 7.3 Access Dashboard
```bash
# Once connected to AP:
# Open browser: http://192.168.4.1:5000
# (or your configured gateway IP)
```

---

## 🔍 Step 8: Monitor and Manage

### 8.1 Real-time Monitoring
```bash
# Web dashboard shows:
# - Connected devices
# - Network bandwidth
# - Camera streams
# - System status
```

### 8.2 Command Line Monitoring
```bash
# Check connected clients:
sudo python3 /opt/radxa/src/ap_manager.py --status

# Monitor network:
python3 /opt/radxa/src/network_monitor.py --interface wlan0

# Check bandwidth:
python3 /opt/radxa/src/bandwidth_calculator.py
```

---

## 🔄 Step 9: System Management

### 9.1 Switch Back to Normal WiFi
```bash
# Via dashboard: Click "Disable AP Mode"

# Or command line:
sudo python3 /opt/radxa/src/ap_manager.py --disable-ap
```

### 9.2 Restart Services
```bash
sudo systemctl restart radxa-manager
sudo systemctl restart radxa-network-monitor
```

### 9.3 View Logs
```bash
# System logs:
sudo journalctl -u radxa-manager --since "1 hour ago"

# Application logs:
tail -f /var/log/radxa/system.log
```

---

## 🛠️ Troubleshooting

### Common Issues:

#### 🔴 SSH Connection Failed
```bash
# Check if SSH is running on Radxa:
sudo systemctl status ssh

# Check firewall:
sudo ufw status

# Try different IP or check network:
ping <radxa-ip>
```

#### 🔴 Services Not Starting
```bash
# Check logs:
sudo journalctl -u radxa-manager -n 50

# Check dependencies:
pip3 list | grep flask

# Reinstall if needed:
sudo /opt/radxa/scripts/install.sh
```

#### 🔴 AP Mode Not Working
```bash
# Check WiFi interface:
ip link show wlan0

# Check hostapd:
sudo systemctl status hostapd
sudo hostapd -dd /etc/hostapd/hostapd.conf

# Check if interface supports AP mode:
iw list | grep -A 10 "Supported interface modes"
```

#### 🔴 Camera Not Detected
```bash
# USB camera:
lsusb
ls /dev/video*

# Check permissions:
sudo usermod -a -G video $USER

# Test camera:
ffmpeg -f v4l2 -i /dev/video0 -t 5 test.mp4
```

#### 🔴 Web Dashboard Not Accessible
```bash
# Check Flask service:
sudo systemctl status radxa-manager

# Check port:
sudo netstat -tlnp | grep :5000

# Check firewall:
sudo ufw allow 5000
```

---

## 🧹 System Maintenance

### Regular Maintenance:
```bash
# Update system:
sudo apt update && sudo apt upgrade

# Check disk space:
df -h

# Clean logs:
sudo journalctl --vacuum-time=7d
```

### Reset System:
```bash
# Quick reset (keeps installation):
sudo /opt/radxa/scripts/reset.sh

# Complete removal:
sudo /opt/radxa/scripts/uninstall.sh
```

---

## 📚 Quick Reference

### Key Commands:
```bash
# Deploy system:
./scripts/deploy.sh <ip> --install --start

# Enable AP mode:
sudo python3 /opt/radxa/src/ap_manager.py --enable-ap

# Disable AP mode:
sudo python3 /opt/radxa/src/ap_manager.py --disable-ap

# Web dashboard:
http://<radxa-ip>:5000

# System status:
sudo systemctl status radxa-manager

# Reset system:
sudo /opt/radxa/scripts/reset.sh

# Remove system:
sudo /opt/radxa/scripts/uninstall.sh
```

### Default Settings:
- **AP SSID:** Radxa_Rock5B_AP
- **AP Password:** radxa12345  
- **AP IP:** 192.168.4.1
- **Web Dashboard:** Port 5000
- **SSH:** Port 22

---

## 🎉 You're Done!

Your Radxa Rock5B+ is now a powerful network management system with:
- ✅ Access Point capabilities
- ✅ Camera streaming
- ✅ Real-time monitoring
- ✅ Web dashboard
- ✅ Bandwidth analysis

Enjoy your new system! 🚀📹
