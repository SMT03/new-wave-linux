#!/bin/bash
# Radxa Rock5B+ System Uninstaller
# Removes all components and reverts system changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}"
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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. This is required for system changes."
    else
        print_error "This script requires root privileges for system changes."
        print_info "Run with: sudo $0"
        exit 1
    fi
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

# Restore original network configurations
restore_network_configs() {
    print_step "Restoring original network configurations..."
    
    # Restore hostapd config
    if [[ -f "/etc/hostapd/hostapd.conf.orig" ]]; then
        print_info "Restoring original hostapd.conf"
        mv "/etc/hostapd/hostapd.conf.orig" "/etc/hostapd/hostapd.conf"
    elif [[ -f "/etc/hostapd/hostapd.conf" ]]; then
        print_info "Removing modified hostapd.conf"
        rm -f "/etc/hostapd/hostapd.conf"
    fi
    
    # Restore dnsmasq config
    if [[ -f "/etc/dnsmasq.conf.orig" ]]; then
        print_info "Restoring original dnsmasq.conf"
        mv "/etc/dnsmasq.conf.orig" "/etc/dnsmasq.conf"
    elif [[ -f "/etc/dnsmasq.conf" ]]; then
        print_info "Removing modified dnsmasq.conf"
        rm -f "/etc/dnsmasq.conf"
    fi
    
    # Restore dhcpcd config
    if [[ -f "/etc/dhcpcd.conf.orig" ]]; then
        print_info "Restoring original dhcpcd.conf"
        mv "/etc/dhcpcd.conf.orig" "/etc/dhcpcd.conf"
    fi
    
    # Restore sysctl config
    if [[ -f "/etc/sysctl.conf.orig" ]]; then
        print_info "Restoring original sysctl.conf"
        mv "/etc/sysctl.conf.orig" "/etc/sysctl.conf"
    fi
}

# Remove iptables rules
remove_iptables_rules() {
    print_step "Removing iptables rules..."
    
    # Remove NAT rules
    print_info "Flushing NAT table..."
    iptables -t nat -F || true
    iptables -t nat -X || true
    
    # Remove filter rules
    print_info "Flushing filter table..."
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

# Reset network interface
reset_network_interface() {
    print_step "Resetting network interface..."
    
    # Reset wlan0 if it exists
    if ip link show wlan0 >/dev/null 2>&1; then
        print_info "Bringing down wlan0..."
        ip link set wlan0 down 2>/dev/null || true
        
        print_info "Flushing wlan0 addresses..."
        ip addr flush dev wlan0 2>/dev/null || true
    fi
    
    # Restart networking
    print_info "Restarting networking service..."
    systemctl restart networking 2>/dev/null || true
    systemctl restart NetworkManager 2>/dev/null || true
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
    
    # Check root privileges
    check_root
    
    # Stop services first
    stop_services
    
    # Remove system components
    remove_services
    remove_configs
    restore_network_configs
    remove_iptables_rules
    reset_network_interface
    
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
    
    print_header "UNINSTALL COMPLETED"
    print_info "✅ All Radxa system components have been removed"
    print_info "✅ Network configurations have been restored"
    print_info "✅ System has been reverted to original state"
    echo
    print_warning "⚠️  A reboot is recommended to ensure all changes take effect"
    echo
    print_info "To reboot now: sudo reboot"
}

# Handle script interruption
trap 'print_error "Uninstall interrupted!"; exit 1' INT TERM

# Run main function
main "$@"
