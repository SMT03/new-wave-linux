# 🚀 Radxa Rock5B+ Network & Camera Management System

A comprehensive management system for Radxa Rock5B+ that provides:
- **Access Point Management**: Switch between AP mode and normal WiFi client mode
- **Live Camera Streaming**: Connect to cameras and stream via RTSP protocol  
- **Real-time Network Monitoring**: Network statistics, client info, DHCP leases
- **Bandwidth Analysis**: Calculate raw CCTV footage requirements
- **Web Dashboard**: Intuitive control panel for all system functions

## ✨ Features

### 🌐 **Network Management**
- One-click AP mode switching
- Real-time client monitoring
- DHCP lease management
- Network interface statistics
- Bandwidth monitoring

### 📹 **Camera Streaming**
- USB camera support
- RTSP server (port 8554)
- Real-time frame rate monitoring
- Multiple camera compatibility
- Live web dashboard preview

### 📊 **System Monitoring**
- CPU, memory, and disk usage
- Network traffic analysis
- Connected devices tracking
- System performance metrics
- Live dashboard updates

### 🎛️ **Easy Management**
- Web-based control panel
- Simple command-line interface
- Systemd service integration
- Automatic startup configuration
- One-command installation

## 🚀 Quick Installation

### **Method 1: Direct Installation (Recommended)**

Run directly on your Radxa Rock5B+:

```bash
# Clone the repository
git clone https://github.com/SMT03/new-wave-linux.git

# Navigate to directory
cd new-wave-linux

# Run installer
./install.sh

# Start the system
radxa start
```

### **Method 2: SSH Deployment**

Deploy from another computer:

```bash
# Clone on your development machine
git clone https://github.com/SMT03/new-wave-linux.git
cd new-wave-linux

# Deploy to Radxa (replace with your Radxa's IP)
./scripts/deploy.sh <radxa-ip> --install --start
```

## 📖 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Detailed installation and configuration
- **[User Guide](docs/USER_GUIDE.md)** - Complete feature documentation

## 🎯 Quick Start

After installation:

```bash
# Start the system
radxa start

# Access web dashboard
# Open browser: http://YOUR_RADXA_IP:5000

# Enable AP mode
radxa enable-ap

# Connect to WiFi: "Radxa_Rock5B_AP" (password: radxa12345)
# Access AP dashboard: http://192.168.4.1:5000
```

## 🔧 Management Commands

```bash
radxa start          # Start all services
radxa stop           # Stop all services
radxa restart        # Restart all services
radxa status         # Check system status
radxa logs           # View system logs
radxa enable-ap      # Enable Access Point mode
radxa disable-ap     # Disable Access Point mode
radxa uninstall      # Remove system completely
radxa reset          # Reset to default settings
```

## 🌐 Access Points

- **Normal Mode**: `http://YOUR_RADXA_IP:5000`
- **AP Mode**: `http://192.168.4.1:5000`
- **RTSP Stream**: `rtsp://YOUR_RADXA_IP:8554/live`

## 📋 System Requirements

- **Hardware**: Radxa Rock5B+ board
- **OS**: Ubuntu 20.04+ (ARM64)
- **Storage**: 32GB+ microSD card
- **Network**: WiFi adapter with AP mode support
- **Camera**: USB camera (optional)
- **Internet**: Required for installation

## 🛠️ What Gets Installed

The installer automatically sets up:

- ✅ **Python Environment**: Virtual environment with all dependencies
- ✅ **System Services**: hostapd, dnsmasq, iptables configuration
- ✅ **Web Dashboard**: Flask-based management interface
- ✅ **RTSP Server**: FFmpeg-based camera streaming
- ✅ **Network Tools**: Monitoring and analysis utilities
- ✅ **Systemd Services**: Automatic startup and management
- ✅ **Firewall Rules**: Security configuration
- ✅ **Management Commands**: Easy-to-use CLI tools

## 🔧 Troubleshooting

### Installation Issues
```bash
# Check installer logs
./install.sh 2>&1 | tee install.log

# Verify system compatibility
uname -a
lsb_release -a
```

### Service Issues
```bash
# Check system status
radxa status

# View detailed logs
radxa logs

# Restart services
radxa restart
```

### Network Issues
```bash
# Check network interfaces
ip addr show

# Test AP mode
radxa enable-ap
iwconfig wlan0
```

For detailed troubleshooting, see the [Deployment Guide](DEPLOYMENT_GUIDE.md).

## 🗑️ Uninstallation

To completely remove the system:

```bash
radxa uninstall
```

This will:
- Stop all services
- Remove installed files
- Restore original network configuration
- Clean up system modifications

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Radxa community for excellent hardware support
- Open source contributors for amazing tools and libraries
- Flask and Python communities for robust web framework

---

**⭐ Star this repository if you find it useful!**
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