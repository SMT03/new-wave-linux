#!/bin/bash

# Local Installation Script for Radxa Rock5B+
# Run this script directly on your Radxa device after cloning the repository

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}                ${BLUE}Radxa Rock5B+ System Installer${NC}                ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

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

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/radxa"
SERVICE_DIR="/etc/systemd/system"
CONFIG_DIR="/etc/radxa"
LOG_DIR="/var/log/radxa"
USER=$(whoami)

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "Don't run this script as root!"
        print_status "Run as regular user, script will use sudo when needed"
        exit 1
    fi
}

# Check if running on correct architecture
check_system() {
    print_step "Checking system compatibility..."
    
    # Check if we're on ARM64 (typical for Rock5B+)
    ARCH=$(uname -m)
    if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
        print_warning "Architecture $ARCH detected. This script is designed for ARM64/aarch64"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check Ubuntu version
    if command -v lsb_release &> /dev/null; then
        OS_VERSION=$(lsb_release -rs)
        print_status "Detected Ubuntu $OS_VERSION"
        if [[ "$OS_VERSION" < "20.04" ]]; then
            print_warning "Ubuntu 20.04+ recommended. Current: $OS_VERSION"
        fi
    fi
    
    print_success "System check completed"
}

# Install system dependencies
install_dependencies() {
    print_step "Installing system dependencies..."
    
    sudo apt update
    
    # Essential packages
    local packages=(
        "python3"
        "python3-pip"
        "python3-venv"
        "hostapd"
        "dnsmasq"
        "iptables"
        "iw"
        "wireless-tools"
        "net-tools"
        "bridge-utils"
        "git"
        "curl"
        "wget"
        "openssh-server"
        "ffmpeg"
        "v4l-utils"
    )
    
    # Optional monitoring packages (install if available)
    local optional_packages=(
        "iftop"
        "htop" 
        "nethogs"
        "vnstat"
        "tcpdump"
        "iperf3"
        "netcat-openbsd"
    )
    
    print_status "Installing essential packages..."
    for package in "${packages[@]}"; do
        if sudo apt install -y "$package"; then
            print_status "✅ Installed $package"
        else
            print_warning "⚠️ Failed to install $package, continuing..."
        fi
    done
    
    print_status "Installing optional monitoring packages..."
    for package in "${optional_packages[@]}"; do
        if sudo apt install -y "$package" 2>/dev/null; then
            print_status "✅ Installed $package"
        else
            print_warning "⚠️ Skipped $package (not available)"
        fi
    done
    
    # Try to install tshark (wireshark terminal interface)
    if sudo apt install -y tshark 2>/dev/null; then
        print_status "✅ Installed tshark"
    else
        print_warning "⚠️ Skipped tshark (not available)"
    fi
    
    print_success "Dependencies installed"
}

# Create directory structure
create_directories() {
    print_step "Creating directory structure..."
    
    sudo mkdir -p "$INSTALL_DIR"
    sudo mkdir -p "$CONFIG_DIR"
    sudo mkdir -p "$LOG_DIR"
    
    # Set permissions
    sudo chown -R $USER:$USER "$INSTALL_DIR"
    sudo chown -R $USER:$USER "$LOG_DIR"
    
    print_success "Directories created"
}

# Copy application files
copy_files() {
    print_step "Copying application files..."
    
    # Copy source files
    cp -r "$SCRIPT_DIR/src" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/web" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/config" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
    
    # Copy configuration files
    sudo cp "$SCRIPT_DIR/config/"*.yaml "$CONFIG_DIR/"
    
    # Copy scripts
    sudo mkdir -p "$INSTALL_DIR/scripts"
    cp "$SCRIPT_DIR/scripts/uninstall.sh" "$INSTALL_DIR/scripts/"
    cp "$SCRIPT_DIR/scripts/reset.sh" "$INSTALL_DIR/scripts/"
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/scripts/"*.sh
    
    print_success "Files copied"
}

# Setup Python environment
setup_python() {
    print_step "Setting up Python environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Python environment configured"
}

# Create systemd services
create_services() {
    print_step "Creating systemd services..."
    
    # Main application service
    cat > /tmp/radxa-system.service << EOF
[Unit]
Description=Radxa Rock5B+ Management System
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python src/web_dashboard.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=radxa-system

[Install]
WantedBy=multi-user.target
EOF

    # Move service file
    sudo mv /tmp/radxa-system.service "$SERVICE_DIR/"
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    print_success "Systemd services created"
}

# Configure network services
configure_network() {
    print_step "Configuring network services..."
    
    # Backup original configurations
    if [[ -f /etc/hostapd/hostapd.conf ]]; then
        sudo cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup
    fi
    
    if [[ -f /etc/dnsmasq.conf ]]; then
        sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
    fi
    
    # Stop and disable conflicting services
    sudo systemctl stop NetworkManager 2>/dev/null || true
    sudo systemctl disable NetworkManager 2>/dev/null || true
    
    # Configure hostapd
    sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
# Radxa Rock5B+ AP Configuration
interface=wlan0
driver=nl80211
ssid=Radxa_Rock5B_AP
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=radxa12345
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

    # Configure dnsmasq
    sudo tee /etc/dnsmasq.conf > /dev/null << EOF
# Radxa Rock5B+ DHCP Configuration
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
dhcp-option=3,192.168.4.1
dhcp-option=6,8.8.8.8,8.8.4.4
server=8.8.8.8
log-queries
log-dhcp
expand-hosts
EOF

    print_success "Network services configured"
}

# Enable services
enable_services() {
    print_step "Enabling services..."
    
    # Enable SSH if not already enabled
    sudo systemctl enable ssh
    sudo systemctl start ssh
    
    # Enable our service (but don't start yet)
    sudo systemctl enable radxa-system
    
    print_success "Services enabled"
}

# Create management commands
create_commands() {
    print_step "Creating management commands..."
    
    # Create radxa command
    sudo tee /usr/local/bin/radxa > /dev/null << EOF
#!/bin/bash
# Radxa Rock5B+ Management Command

case "\$1" in
    start)
        sudo systemctl start radxa-system
        echo "Radxa system started"
        ;;
    stop)
        sudo systemctl stop radxa-system
        echo "Radxa system stopped"
        ;;
    restart)
        sudo systemctl restart radxa-system
        echo "Radxa system restarted"
        ;;
    status)
        sudo systemctl status radxa-system
        ;;
    logs)
        sudo journalctl -u radxa-system -f
        ;;
    enable-ap)
        cd $INSTALL_DIR && source venv/bin/activate && python src/ap_manager.py --enable-ap
        ;;
    disable-ap)
        cd $INSTALL_DIR && source venv/bin/activate && python src/ap_manager.py --disable-ap
        ;;
    uninstall)
        $INSTALL_DIR/scripts/uninstall.sh
        ;;
    reset)
        $INSTALL_DIR/scripts/reset.sh
        ;;
    *)
        echo "Usage: radxa {start|stop|restart|status|logs|enable-ap|disable-ap|uninstall|reset}"
        exit 1
        ;;
esac
EOF

    sudo chmod +x /usr/local/bin/radxa
    
    print_success "Management commands created"
}

# Set up firewall rules
setup_firewall() {
    print_step "Setting up firewall rules..."
    
    # Allow SSH
    sudo ufw allow ssh 2>/dev/null || true
    
    # Allow web dashboard
    sudo ufw allow 5000/tcp 2>/dev/null || true
    
    # Allow RTSP
    sudo ufw allow 8554/tcp 2>/dev/null || true
    
    print_success "Firewall configured"
}

# Main installation function
main() {
    print_header
    
    print_status "Starting Radxa Rock5B+ System Installation..."
    echo ""
    
    check_root
    check_system
    install_dependencies
    create_directories
    copy_files
    setup_python
    create_services
    configure_network
    enable_services
    create_commands
    setup_firewall
    
    echo ""
    print_success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_success "                        INSTALLATION COMPLETED!                           "
    print_success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${GREEN}🎉 Radxa Rock5B+ Management System is now installed!${NC}"
    echo ""
    echo -e "${BLUE}📋 NEXT STEPS:${NC}"
    echo ""
    echo -e "${YELLOW}1️⃣ START THE SYSTEM:${NC}"
    echo "   radxa start"
    echo ""
    echo -e "${YELLOW}2️⃣ ACCESS WEB DASHBOARD:${NC}"
    echo "   http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo -e "${YELLOW}3️⃣ ENABLE AP MODE:${NC}"
    echo "   radxa enable-ap"
    echo ""
    echo -e "${YELLOW}4️⃣ USEFUL COMMANDS:${NC}"
    echo "   radxa status          # Check system status"
    echo "   radxa logs           # View system logs"
    echo "   radxa restart        # Restart system"
    echo "   radxa disable-ap     # Disable AP mode"
    echo "   radxa uninstall      # Remove system"
    echo ""
    echo -e "${GREEN}✨ Installation completed successfully!${NC}"
}

# Run main function
main "$@"
