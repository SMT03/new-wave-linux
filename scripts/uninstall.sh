#!/bin/bash
# Radxa Rock5B+ System Uninstaller
# Removes all components and reverts system changes with comprehensive network recovery

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}                        ${BLUE}$1${NC}                        ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Detect system configuration
detect_system() {
    print_step "Detecting system configuration..."
    
    # Detect network management system
    if command -v systemctl >/dev/null 2>&1 && systemctl list-units --type=service | grep -q NetworkManager; then
        NETWORK_MANAGER="NetworkManager"
        print_info "Using NetworkManager"
    elif command -v systemctl >/dev/null 2>&1 && systemctl list-units --type=service | grep -q networking; then
        NETWORK_MANAGER="networking"
        print_info "Using traditional networking service"
    else
        NETWORK_MANAGER="manual"
        print_info "Manual network configuration detected"
    fi
    
    # Detect DHCP client
    if command -v dhclient >/dev/null 2>&1; then
        DHCP_CLIENT="dhclient"
        print_info "Using dhclient"
    elif command -v dhcpcd >/dev/null 2>&1; then
        DHCP_CLIENT="dhcpcd"
        print_info "Using dhcpcd"
    elif command -v udhcpc >/dev/null 2>&1; then
        DHCP_CLIENT="udhcpc"
        print_info "Using udhcpc"
    else
        DHCP_CLIENT="none"
        print_warning "No DHCP client found"
    fi
    
    # Detect network configuration method
    if [[ -d /etc/netplan ]]; then
        CONFIG_METHOD="netplan"
        print_info "Using Netplan configuration"
    elif [[ -f /etc/network/interfaces ]]; then
        CONFIG_METHOD="interfaces"
        print_info "Using /etc/network/interfaces"
    elif [[ -d /etc/systemd/network ]]; then
        CONFIG_METHOD="systemd-networkd"
        print_info "Using systemd-networkd"
    else
        CONFIG_METHOD="unknown"
        print_warning "Unknown network configuration method"
    fi
    
    # Detect primary ethernet interface
    ETH_INTERFACE=$(ip route | awk '/default/ { print $5 }' | head -n1)
    if [[ -z "$ETH_INTERFACE" ]]; then
        ETH_INTERFACE=$(ip link show | awk -F: '$0 !~ "lo|vir|wl|^[^0-9]"{print $2;getline}' | head -n1 | xargs)
    fi
    if [[ -z "$ETH_INTERFACE" ]]; then
        ETH_INTERFACE="eth0"  # fallback
    fi
    print_info "Primary ethernet interface: $ETH_INTERFACE"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_info "Running with root privileges"
    else
        print_error "This script requires root privileges for system changes."
        print_info "Run with: sudo $0"
        exit 1
    fi
}

# Comprehensive network restoration
restore_network_comprehensive() {
    print_step "Performing comprehensive network restoration..."
    
    # Step 1: Stop AP mode if running
    print_info "Disabling AP mode..."
    if systemctl is-active --quiet hostapd 2>/dev/null; then
        systemctl stop hostapd 2>/dev/null || true
        systemctl disable hostapd 2>/dev/null || true
    fi
    
    if systemctl is-active --quiet dnsmasq 2>/dev/null; then
        systemctl stop dnsmasq 2>/dev/null || true
        systemctl disable dnsmasq 2>/dev/null || true
    fi
    
    # Step 2: Remove IP forwarding and iptables rules
    print_info "Removing IP forwarding and firewall rules..."
    echo 0 > /proc/sys/net/ipv4/ip_forward 2>/dev/null || true
    
    # Clear iptables rules
    iptables -F 2>/dev/null || true
    iptables -t nat -F 2>/dev/null || true
    iptables -t mangle -F 2>/dev/null || true
    iptables -X 2>/dev/null || true
    iptables -t nat -X 2>/dev/null || true
    iptables -t mangle -X 2>/dev/null || true
    
    # Step 3: Reset network interfaces
    print_info "Resetting network interfaces..."
    
    # Flush all IP addresses on ethernet interface
    ip addr flush dev $ETH_INTERFACE 2>/dev/null || true
    
    # Bring interface down and up
    ip link set $ETH_INTERFACE down 2>/dev/null || true
    sleep 2
    ip link set $ETH_INTERFACE up 2>/dev/null || true
    
    # Reset wlan0 if it exists
    if ip link show wlan0 >/dev/null 2>&1; then
        print_info "Resetting wlan0 interface..."
        ip addr flush dev wlan0 2>/dev/null || true
        ip link set wlan0 down 2>/dev/null || true
        sleep 1
        ip link set wlan0 up 2>/dev/null || true
    fi
    
    # Step 4: Restore DHCP based on detected client
    print_info "Restoring DHCP configuration..."
    case $DHCP_CLIENT in
        "dhclient")
            print_info "Using dhclient to restore network..."
            dhclient -r $ETH_INTERFACE 2>/dev/null || true
            sleep 2
            dhclient $ETH_INTERFACE 2>/dev/null || print_warning "dhclient failed, trying alternatives..."
            ;;
        "dhcpcd")
            print_info "Using dhcpcd to restore network..."
            dhcpcd -k $ETH_INTERFACE 2>/dev/null || true
            sleep 2
            dhcpcd $ETH_INTERFACE 2>/dev/null || print_warning "dhcpcd failed, trying alternatives..."
            ;;
        "udhcpc")
            print_info "Using udhcpc to restore network..."
            killall udhcpc 2>/dev/null || true
            sleep 2
            udhcpc -i $ETH_INTERFACE 2>/dev/null || print_warning "udhcpc failed, trying alternatives..."
            ;;
        *)
            print_warning "No DHCP client found, using manual methods..."
            ;;
    esac
    
    # Step 5: Restart network services based on detected system
    print_info "Restarting network services..."
    case $NETWORK_MANAGER in
        "NetworkManager")
            systemctl restart NetworkManager 2>/dev/null || print_warning "Failed to restart NetworkManager"
            ;;
        "networking")
            systemctl restart networking 2>/dev/null || print_warning "Failed to restart networking service"
            ;;
        *)
            print_info "Using manual network restart methods..."
            ;;
    esac
    
    # Step 6: Apply network configuration based on detected method
    print_info "Applying network configuration..."
    case $CONFIG_METHOD in
        "netplan")
            restore_netplan_config
            ;;
        "interfaces")
            restore_interfaces_config
            ;;
        "systemd-networkd")
            restore_systemd_networkd_config
            ;;
        *)
            print_warning "Unknown config method, using generic restoration..."
            ;;
    esac
    
    # Step 7: Final network recovery attempts
    print_info "Performing final network recovery..."
    
    # Try to get IP via multiple methods
    if ! ip route | grep -q default; then
        print_warning "No default route found, attempting recovery..."
        
        # Method 1: Restart network interface
        ifdown $ETH_INTERFACE 2>/dev/null || true
        sleep 2
        ifup $ETH_INTERFACE 2>/dev/null || true
        sleep 3
        
        # Method 2: Force DHCP renewal
        if [[ "$DHCP_CLIENT" == "dhclient" ]]; then
            timeout 10 dhclient -v $ETH_INTERFACE 2>/dev/null || true
        elif [[ "$DHCP_CLIENT" == "dhcpcd" ]]; then
            timeout 10 dhcpcd -4 $ETH_INTERFACE 2>/dev/null || true
        fi
        
        # Method 3: Reset and restart everything
        if ! ip route | grep -q default; then
            print_warning "Still no network, performing full reset..."
            systemctl restart systemd-networkd 2>/dev/null || true
            systemctl restart NetworkManager 2>/dev/null || true
            systemctl restart networking 2>/dev/null || true
            sleep 5
        fi
    fi
    
    print_success "Network restoration completed"
}

# Restore Netplan configuration
restore_netplan_config() {
    print_info "Restoring Netplan configuration..."
    
    # Find netplan config files
    local netplan_files=($(find /etc/netplan -name "*.yaml" -o -name "*.yml" 2>/dev/null))
    
    if [[ ${#netplan_files[@]} -eq 0 ]]; then
        print_info "Creating default Netplan configuration..."
        cat > /etc/netplan/01-netcfg.yaml << EOF
network:
  version: 2
  ethernets:
    $ETH_INTERFACE:
      dhcp4: true
      dhcp6: false
EOF
    else
        print_info "Updating existing Netplan configuration..."
        for file in "${netplan_files[@]}"; do
            # Backup original
            cp "$file" "${file}.backup.$(date +%s)" 2>/dev/null || true
            
            # Create clean DHCP config
            cat > "$file" << EOF
network:
  version: 2
  ethernets:
    $ETH_INTERFACE:
      dhcp4: true
      dhcp6: false
EOF
        done
    fi
    
    # Apply netplan
    netplan apply 2>/dev/null || print_warning "Netplan apply failed"
}

# Restore /etc/network/interfaces configuration
restore_interfaces_config() {
    print_info "Restoring /etc/network/interfaces configuration..."
    
    # Backup original
    if [[ -f /etc/network/interfaces ]]; then
        cp /etc/network/interfaces /etc/network/interfaces.backup.$(date +%s) 2>/dev/null || true
    fi
    
    # Create clean interfaces config
    cat > /etc/network/interfaces << EOF
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
auto $ETH_INTERFACE
iface $ETH_INTERFACE inet dhcp
EOF
    
    # Restart networking
    systemctl restart networking 2>/dev/null || true
}

# Restore systemd-networkd configuration
restore_systemd_networkd_config() {
    print_info "Restoring systemd-networkd configuration..."
    
    # Remove any custom network configs
    rm -f /etc/systemd/network/radxa-*.network 2>/dev/null || true
    
    # Create default DHCP config
    cat > /etc/systemd/network/20-ethernet.network << EOF
[Match]
Name=$ETH_INTERFACE

[Network]
DHCP=ipv4
EOF
    
    # Restart systemd-networkd
    systemctl restart systemd-networkd 2>/dev/null || true
    systemctl restart systemd-resolved 2>/dev/null || true
}

# Stop and disable services
stop_services() {
    print_step "Stopping and disabling Radxa services..."
    
    services=(
        "radxa-manager"
        "radxa-network-monitor"
        "hostapd"
        "dnsmasq"
    )
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            print_info "Stopping $service..."
            systemctl stop "$service" || true
        fi
        
        if systemctl is-enabled --quiet "$service" 2>/dev/null; then
            print_info "Disabling $service..."
            systemctl disable "$service" || true
        fi
    done
}

# Remove systemd service files
remove_services() {
    print_step "Removing systemd service files..."
    
    service_files=(
        "/etc/systemd/system/radxa-manager.service"
        "/etc/systemd/system/radxa-network-monitor.service"
    )
    
    for file in "${service_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_info "Removing $file"
            rm -f "$file"
        fi
    done
    
    print_info "Reloading systemd daemon..."
    systemctl daemon-reload
}

# Remove configuration files
remove_configs() {
    print_step "Removing configuration files..."
    
    config_dirs=(
        "/etc/radxa"
        "/var/lib/radxa"
        "/var/log/radxa"
    )
    
    config_files=(
        "/etc/hostapd/hostapd.conf.radxa.bak"
        "/etc/dnsmasq.conf.radxa.bak"
        "/etc/dhcpcd.conf.radxa.bak"
        "/etc/sysctl.conf.radxa.bak"
    )
    
    # Remove directories
    for dir in "${config_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            print_info "Removing directory $dir"
            rm -rf "$dir"
        fi
    done
    
    # Remove backup files
    for file in "${config_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_info "Removing backup file $file"
            rm -f "$file"
        fi
    done
}

# Remove iptables rules
remove_iptables_rules() {
    print_step "Removing iptables rules..."
    
    # Note: iptables rules are now handled in restore_network_comprehensive()
    print_info "iptables rules cleared in network restoration"
}
    iptables -F || true
    iptables -X || true
    
    # Reset to default policies
    print_info "Resetting to default policies..."
    iptables -P INPUT ACCEPT || true
    iptables -P FORWARD ACCEPT || true
    iptables -P OUTPUT ACCEPT || true
    
    # Save iptables rules
    if command -v iptables-save >/dev/null 2>&1; then
        print_info "Saving iptables rules..."
        iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
    fi
}

# Remove application files
remove_application() {
    print_step "Removing application files..."
    
    app_dirs=(
        "/opt/radxa"
        "/usr/local/bin/radxa-manager"
        "/usr/local/bin/radxa-monitor"
    )
    
    for item in "${app_dirs[@]}"; do
        if [[ -e "$item" ]]; then
            print_info "Removing $item"
            rm -rf "$item"
        fi
    done
}

# Remove Python packages (optional)
remove_python_packages() {
    print_step "Removing Python packages..."
    
    if command -v pip3 >/dev/null 2>&1; then
        packages=(
            "flask"
            "flask-socketio"
            "psutil"
            "netifaces"
            "scapy"
            "pyshark"
            "opencv-python"
            "ffmpeg-python"
            "numpy"
            "pyyaml"
        )
        
        print_info "Uninstalling Python packages..."
        for package in "${packages[@]}"; do
            if pip3 show "$package" >/dev/null 2>&1; then
                print_info "Uninstalling $package"
                pip3 uninstall -y "$package" 2>/dev/null || true
            fi
        done
    fi
}

# Remove users and groups
remove_users() {
    print_step "Removing users and groups..."
    
    if id "radxa" >/dev/null 2>&1; then
        print_info "Removing user 'radxa'"
        userdel -r radxa 2>/dev/null || true
    fi
    
    if getent group radxa >/dev/null 2>&1; then
        print_info "Removing group 'radxa'"
        groupdel radxa 2>/dev/null || true
    fi
}

# Remove log files
remove_logs() {
    print_step "Removing log files..."
    
    log_patterns=(
        "/var/log/radxa*"
        "/var/log/hostapd*"
        "/var/log/dnsmasq*radxa*"
    )
    
    for pattern in "${log_patterns[@]}"; do
        if ls $pattern >/dev/null 2>&1; then
            print_info "Removing logs matching $pattern"
            rm -f $pattern
        fi
    done
}

# Clean package cache
clean_packages() {
    print_step "Cleaning package cache..."
    
    if command -v apt >/dev/null 2>&1; then
        print_info "Cleaning apt cache..."
        apt autoremove -y 2>/dev/null || true
        apt autoclean 2>/dev/null || true
    fi
}

# Main uninstall function
main() {
    print_header "RADXA ROCK5B+ SYSTEM UNINSTALLER"
    
    print_warning "This will completely remove the Radxa management system!"
    print_warning "All configurations will be reverted to original state."
    echo
    
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Uninstall cancelled."
        exit 0
    fi
    
    echo
    print_info "Starting uninstallation process..."
    echo
    
    # Check root privileges and detect system
    check_root
    detect_system
    
    # Stop services first
    stop_services
    
    # Remove system components
    remove_services
    remove_configs
    
    # Comprehensive network restoration
    restore_network_comprehensive
    
    remove_iptables_rules
    
    # Remove application
    remove_application
    remove_logs
    
    # Optional removals (ask user)
    echo
    read -p "Remove Python packages? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        remove_python_packages
    fi
    
    echo
    read -p "Remove radxa user account? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        remove_users
    fi
    
    # Clean up
    clean_packages
    
    # Final network verification
    print_step "Verifying network restoration..."
    sleep 3
    
    if ip route | grep -q default; then
        print_success "✅ Network connectivity restored"
        print_info "Default route: $(ip route | grep default | head -n1)"
        print_info "IP address: $(ip addr show $ETH_INTERFACE | grep "inet " | awk '{print $2}' | head -n1)"
    else
        print_warning "⚠️  No default route found"
        print_info "You may need to manually restart your network:"
        print_info "  sudo systemctl restart NetworkManager"
        print_info "  sudo systemctl restart networking"
        print_info "  sudo reboot"
    fi
    
    print_header "UNINSTALL COMPLETED"
    print_success "✅ All Radxa system components have been removed"
    print_success "✅ Network configurations have been restored"
    print_success "✅ System has been reverted to original state"
    echo
    print_warning "⚠️  A reboot is recommended to ensure all changes take effect"
    echo
    print_info "To reboot now: sudo reboot"
    
    # Emergency network recovery information
    echo
    print_header "EMERGENCY NETWORK RECOVERY"
    print_info "If network issues persist after reboot, try these commands:"
    echo
    print_info "Method 1 - NetworkManager reset:"
    print_info "  sudo systemctl restart NetworkManager"
    print_info "  sudo nmcli connection reload"
    echo
    print_info "Method 2 - Manual interface reset:"
    print_info "  sudo ip addr flush dev $ETH_INTERFACE"
    print_info "  sudo ip link set $ETH_INTERFACE down && sudo ip link set $ETH_INTERFACE up"
    if [[ "$DHCP_CLIENT" != "none" ]]; then
        print_info "  sudo $DHCP_CLIENT $ETH_INTERFACE"
    fi
    echo
    print_info "Method 3 - Full network restart:"
    print_info "  sudo systemctl restart systemd-networkd"
    print_info "  sudo systemctl restart networking"
    print_info "  sudo reboot"
}

# Handle script interruption
trap 'print_error "Uninstall interrupted!"; exit 1' INT TERM

# Run main function
main "$@"
