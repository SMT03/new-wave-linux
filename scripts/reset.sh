#!/bin/bash
# Quick System Reset Script
# For development - quickly reset system without full uninstall

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🔄 Quick System Reset"
echo "===================="

# Stop services
print_info "Stopping services..."
sudo systemctl stop radxa-manager 2>/dev/null || true
sudo systemctl stop radxa-network-monitor 2>/dev/null || true
sudo systemctl stop hostapd 2>/dev/null || true
sudo systemctl stop dnsmasq 2>/dev/null || true

# Reset network interface
print_info "Resetting network interface..."
sudo ip link set wlan0 down 2>/dev/null || true
sudo ip addr flush dev wlan0 2>/dev/null || true

# Clear iptables rules
print_info "Clearing iptables rules..."
sudo iptables -t nat -F 2>/dev/null || true
sudo iptables -F 2>/dev/null || true

# Restart networking
print_info "Restarting networking..."
sudo systemctl restart networking 2>/dev/null || true
sudo systemctl restart NetworkManager 2>/dev/null || true

print_info "✅ Quick reset completed"
print_warning "System is back to normal network mode"
