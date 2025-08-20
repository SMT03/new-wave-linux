# 🚀 Radxa Rock5B+ Management System - Quick Install

## One-Command Installation

Clone and install directly on your Radxa Rock5B+:

```bash
# Clone the repository
git clone https://github.com/SMT03/new-wave-linux.git

# Navigate to directory
cd new-wave-linux

# Run installation
./install.sh
```

That's it! The script will:
- ✅ Check system compatibility
- ✅ Install all dependencies
- ✅ Set up Python environment
- ✅ Configure network services
- ✅ Create systemd services
- ✅ Set up management commands

## Quick Start

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

## Management Commands

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

## System Features

- 🌐 **AP Mode Management**: Switch between AP and client modes
- 📹 **Camera Streaming**: RTSP streaming with frame rate monitoring
- 📊 **Network Monitoring**: Bandwidth, clients, DHCP leases
- 🎛️ **Web Dashboard**: Real-time system control and monitoring
- ⚡ **Easy Management**: Simple command-line interface

## Requirements

- Radxa Rock5B+ with Ubuntu 20.04+
- WiFi adapter with AP mode support
- Internet connection for installation

## Troubleshooting

If you encounter issues:

1. **Check logs**: `radxa logs`
2. **Verify status**: `radxa status`
3. **Restart system**: `radxa restart`
4. **Reset configuration**: `radxa reset`

For detailed troubleshooting, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

**Need the old SSH deployment method?** See [scripts/deploy.sh](scripts/deploy.sh)
