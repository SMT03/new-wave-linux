#!/bin/bash

# Radxa Rock5B+ Network & Camera Management System
# Installation Script

set -e

echo "🚀 Installing Radxa Rock5B+ Network & Camera Management System"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
    exit 1
fi

# Check if running on supported system
if ! command -v apt &> /dev/null; then
    print_error "This script requires a Debian/Ubuntu-based system with apt package manager."
    exit 1
fi

print_status "Checking system compatibility..."

# Detect architecture
ARCH=$(uname -m)
print_status "Detected architecture: $ARCH"

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    pkg-config

# Install network management tools
print_status "Installing network management tools..."
sudo apt install -y \
    hostapd \
    dnsmasq \
    dhcpcd5 \
    iptables-persistent \
    bridge-utils \
    wireless-tools \
    wpasupplicant \
    net-tools \
    iproute2

# Install monitoring tools
print_status "Installing monitoring tools..."
sudo apt install -y \
    iftop \
    htop \
    nethogs \
    vnstat \
    tcpdump \
    wireshark-cli \
    iperf3 \
    netcat-openbsd \
    ss

# Install multimedia packages
print_status "Installing multimedia packages..."
sudo apt install -y \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    v4l-utils \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly

# Install OpenCV dependencies
print_status "Installing OpenCV dependencies..."
sudo apt install -y \
    libopencv-dev \
    python3-opencv \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libgtk-3-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev

# Install web server dependencies
print_status "Installing web server dependencies..."
sudo apt install -y \
    nginx \
    supervisor

# Create system directories
print_status "Creating system directories..."
sudo mkdir -p /etc/radxa
sudo mkdir -p /var/log/radxa
sudo mkdir -p /var/lib/radxa
sudo mkdir -p /opt/radxa

# Create Python virtual environment
VENV_PATH="/opt/radxa/venv"
print_status "Creating Python virtual environment at $VENV_PATH..."
sudo python3 -m venv $VENV_PATH
sudo chown -R $USER:$USER $VENV_PATH

# Activate virtual environment and install Python packages
print_status "Installing Python packages..."
source $VENV_PATH/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required Python packages
pip install \
    psutil>=5.9.0 \
    netifaces>=0.11.0 \
    scapy>=2.4.5 \
    pyshark>=0.6.0 \
    speedtest-cli>=2.1.3 \
    opencv-python>=4.8.0 \
    ffmpeg-python>=0.2.0 \
    numpy>=1.24.0 \
    Pillow>=10.0.0 \
    imageio>=2.31.0 \
    flask>=2.3.0 \
    flask-socketio>=5.3.0 \
    requests>=2.31.0 \
    pyyaml>=6.0 \
    configparser>=5.3.0 \
    aiohttp>=3.8.0 \
    websockets>=11.0 \
    click>=8.1.0 \
    colorama>=0.4.6 \
    python-dateutil>=2.8.2

deactivate

print_success "Python packages installed successfully"

# Copy configuration files
print_status "Installing configuration files..."
sudo cp config/settings.yaml /etc/radxa/settings.yaml
sudo chmod 644 /etc/radxa/settings.yaml

# Copy source files
print_status "Installing application files..."
sudo cp -r src/* /opt/radxa/
sudo chmod +x /opt/radxa/*.py

# Create systemd service files
print_status "Creating systemd services..."

# Main service
cat << EOF | sudo tee /etc/systemd/system/radxa-manager.service > /dev/null
[Unit]
Description=Radxa Rock5B+ Network & Camera Management System
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/radxa
Environment=PYTHONPATH=/opt/radxa
ExecStart=$VENV_PATH/bin/python /opt/radxa/web_dashboard.py --config /etc/radxa/settings.yaml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Network monitor service
cat << EOF | sudo tee /etc/systemd/system/radxa-network-monitor.service > /dev/null
[Unit]
Description=Radxa Network Monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/radxa
Environment=PYTHONPATH=/opt/radxa
ExecStart=$VENV_PATH/bin/python /opt/radxa/network_monitor.py --continuous --config /etc/radxa/settings.yaml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Create command line aliases
print_status "Creating command line tools..."
cat << EOF | sudo tee /usr/local/bin/radxa-ap > /dev/null
#!/bin/bash
$VENV_PATH/bin/python /opt/radxa/ap_manager.py --config /etc/radxa/settings.yaml "\$@"
EOF

cat << EOF | sudo tee /usr/local/bin/radxa-camera > /dev/null
#!/bin/bash
$VENV_PATH/bin/python /opt/radxa/camera_streamer.py --config /etc/radxa/settings.yaml "\$@"
EOF

cat << EOF | sudo tee /usr/local/bin/radxa-network > /dev/null
#!/bin/bash
$VENV_PATH/bin/python /opt/radxa/network_monitor.py --config /etc/radxa/settings.yaml "\$@"
EOF

sudo chmod +x /usr/local/bin/radxa-*

# Configure nginx (optional)
print_status "Configuring nginx reverse proxy..."
cat << EOF | sudo tee /etc/nginx/sites-available/radxa-dashboard > /dev/null
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/radxa-dashboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t && sudo systemctl restart nginx

# Set up log rotation
print_status "Configuring log rotation..."
cat << EOF | sudo tee /etc/logrotate.d/radxa > /dev/null
/var/log/radxa/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Create user groups for hardware access
print_status "Configuring user permissions..."
sudo usermod -a -G video $USER
sudo usermod -a -G audio $USER
sudo usermod -a -G dialout $USER

# Setup udev rules for camera access
cat << EOF | sudo tee /etc/udev/rules.d/99-radxa-camera.rules > /dev/null
# Allow users in video group to access video devices
SUBSYSTEM=="video4linux", GROUP="video", MODE="0664"
KERNEL=="video[0-9]*", GROUP="video", MODE="0664"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger

# Enable and start services
print_status "Enabling system services..."
sudo systemctl enable radxa-manager.service
sudo systemctl enable radxa-network-monitor.service
sudo systemctl enable nginx

# Create startup script
print_status "Creating management scripts..."
cat << EOF | sudo tee /usr/local/bin/radxa-start > /dev/null
#!/bin/bash
echo "Starting Radxa Rock5B+ Management System..."
sudo systemctl start radxa-manager
sudo systemctl start radxa-network-monitor
sudo systemctl start nginx
echo "Services started. Web dashboard available at http://\$(hostname -I | awk '{print \$1}'):8080"
EOF

cat << EOF | sudo tee /usr/local/bin/radxa-stop > /dev/null
#!/bin/bash
echo "Stopping Radxa Rock5B+ Management System..."
sudo systemctl stop radxa-manager
sudo systemctl stop radxa-network-monitor
echo "Services stopped."
EOF

cat << EOF | sudo tee /usr/local/bin/radxa-status > /dev/null
#!/bin/bash
echo "Radxa Rock5B+ Management System Status:"
echo "======================================="
echo "Main Service:"
sudo systemctl status radxa-manager --no-pager -l
echo ""
echo "Network Monitor:"
sudo systemctl status radxa-network-monitor --no-pager -l
echo ""
echo "Web Interface: http://\$(hostname -I | awk '{print \$1}'):8080"
EOF

sudo chmod +x /usr/local/bin/radxa-start
sudo chmod +x /usr/local/bin/radxa-stop
sudo chmod +x /usr/local/bin/radxa-status

# Final system configuration
print_status "Applying final configurations..."

# Enable IP forwarding for AP mode
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

# Create backup of original configurations
sudo cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup 2>/dev/null || true
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null || true

print_success "Installation completed successfully!"
echo ""
echo "📋 Installation Summary:"
echo "======================="
echo "✅ System packages installed"
echo "✅ Python environment created at $VENV_PATH"
echo "✅ Application installed to /opt/radxa"
echo "✅ Configuration file: /etc/radxa/settings.yaml"
echo "✅ Systemd services created and enabled"
echo "✅ Command line tools installed"
echo "✅ Nginx reverse proxy configured"
echo "✅ Log rotation configured"
echo ""
echo "🎮 Available Commands:"
echo "====================="
echo "radxa-start          - Start all services"
echo "radxa-stop           - Stop all services"
echo "radxa-status         - Show service status"
echo "radxa-ap             - Access Point management"
echo "radxa-camera         - Camera control"
echo "radxa-network        - Network monitoring"
echo ""
echo "🌐 Web Interface:"
echo "================="
echo "URL: http://$(hostname -I | awk '{print $1}'):8080"
echo "The web dashboard provides a complete control interface"
echo ""
echo "🚀 Quick Start:"
echo "==============="
echo "1. Start services: sudo radxa-start"
echo "2. Open web browser to the URL above"
echo "3. Use the dashboard to control AP and camera functions"
echo ""
echo "📖 Configuration:"
echo "=================="
echo "Edit /etc/radxa/settings.yaml to customize settings"
echo "Restart services after configuration changes"
echo ""

# Ask if user wants to start services now
read -p "Would you like to start the services now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting services..."
    sudo systemctl start radxa-manager
    sudo systemctl start radxa-network-monitor
    sudo systemctl start nginx
    print_success "Services started successfully!"
    echo "Web dashboard is now available at: http://$(hostname -I | awk '{print $1}'):8080"
else
    echo "Services not started. Use 'radxa-start' when ready."
fi

print_success "Setup complete! Enjoy your Radxa Rock5B+ management system! 🎉"
