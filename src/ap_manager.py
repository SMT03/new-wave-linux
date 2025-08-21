#!/usr/bin/env python3
"""
Access Point Manager for Radxa Rock5B+
Handles switching between AP mode and normal WiFi client mode
"""

import os
import sys
import subprocess
import time
import argparse
import logging
from pathlib import Path
import yaml
import psutil
import netifaces

# Auto-detect config path
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "settings.yaml"

class APManager:
    """
    Manages WiFi Access Point functionality for Radxa Rock5B+
    """
    
    def __init__(self, config_path=None):
        """
        Initialize AP Manager
        
        Args:
            config_path: Path to configuration file (auto-detected if None)
        """
        if config_path is None:
            config_path = str(CONFIG_PATH)
        self.config = self.load_config(config_path)
        self.wifi_interface = self.config['network']['wifi_interface']
        self.ap_config = self.config['network']['ap_config']
        self.logger = self.setup_logging()
        
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
            
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
        
    def run_command(self, command, check=True):
        """Execute shell command and return result"""
        try:
            result = subprocess.run(
                command.split(), 
                capture_output=True, 
                text=True, 
                check=check
            )
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {command}")
            self.logger.error(f"Error: {e.stderr}")
            return None, e.stderr
            
    def check_interface_exists(self, interface):
        """Check if network interface exists"""
        return interface in netifaces.interfaces()
        
    def get_interface_status(self, interface):
        """Get status of network interface"""
        try:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            
            if interface in stats:
                return {
                    'exists': True,
                    'is_up': stats[interface].isup,
                    'speed': stats[interface].speed,
                    'addresses': addrs.get(interface, [])
                }
        except Exception as e:
            self.logger.error(f"Error getting interface status: {e}")
            
        return {'exists': False}
        
    def stop_network_services(self):
        """Stop network services before switching modes"""
        services = ['hostapd', 'dnsmasq', 'dhcpcd']
        
        for service in services:
            self.logger.info(f"Stopping {service}")
            self.run_command(f"sudo systemctl stop {service}", check=False)
            
    def enable_ap_mode(self):
        """Enable Access Point mode"""
        self.logger.info("Enabling AP mode...")
        
        # Check if WiFi interface exists
        if not self.check_interface_exists(self.wifi_interface):
            self.logger.error(f"WiFi interface {self.wifi_interface} not found")
            return False
            
        # Stop existing network services
        self.stop_network_services()
        
        # Configure hostapd
        self.create_hostapd_config()
        
        # Configure dnsmasq
        self.create_dnsmasq_config()
        
        # Set static IP for WiFi interface
        self.configure_interface_ip()
        
        # Enable IP forwarding
        self.enable_ip_forwarding()
        
        # Configure iptables for NAT
        self.configure_nat()
        
        # Start services
        return self.start_ap_services()
        
    def create_hostapd_config(self):
        """Create hostapd configuration file"""
        config_content = f"""interface={self.wifi_interface}
driver=nl80211
ssid={self.ap_config['ssid']}
hw_mode=g
channel={self.ap_config['channel']}
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self.ap_config['password']}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        
        config_path = "/etc/hostapd/hostapd.conf"
        try:
            with open(config_path, 'w') as f:
                f.write(config_content)
            self.logger.info(f"Created hostapd config: {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create hostapd config: {e}")
            return False
            
    def create_dnsmasq_config(self):
        """Create dnsmasq configuration file"""
        config_content = f"""interface={self.wifi_interface}
dhcp-range={self.ap_config['dhcp_start']},{self.ap_config['dhcp_end']},255.255.255.0,24h
"""
        
        config_path = "/etc/dnsmasq.conf"
        try:
            # Backup original config
            self.run_command(f"sudo cp {config_path} {config_path}.backup", check=False)
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            self.logger.info(f"Created dnsmasq config: {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create dnsmasq config: {e}")
            return False
            
    def configure_interface_ip(self):
        """Configure static IP for WiFi interface"""
        gateway_ip = self.ap_config['gateway']
        
        commands = [
            f"sudo ip addr flush dev {self.wifi_interface}",
            f"sudo ip addr add {gateway_ip}/24 dev {self.wifi_interface}",
            f"sudo ip link set {self.wifi_interface} up"
        ]
        
        for cmd in commands:
            stdout, stderr = self.run_command(cmd, check=False)
            if stderr:
                self.logger.warning(f"Command warning: {cmd} - {stderr}")
                
        self.logger.info(f"Configured {self.wifi_interface} with IP {gateway_ip}")
        
    def enable_ip_forwarding(self):
        """Enable IP forwarding for NAT"""
        self.run_command("sudo sysctl net.ipv4.ip_forward=1")
        
        # Make it permanent
        sysctl_conf = "/etc/sysctl.conf"
        try:
            with open(sysctl_conf, 'r') as f:
                content = f.read()
                
            if "net.ipv4.ip_forward=1" not in content:
                with open(sysctl_conf, 'a') as f:
                    f.write("\nnet.ipv4.ip_forward=1\n")
                    
        except Exception as e:
            self.logger.error(f"Failed to update sysctl.conf: {e}")
            
    def configure_nat(self):
        """Configure iptables for NAT"""
        eth_interface = self.config['network']['ethernet_interface']
        
        # Clear existing rules
        self.run_command("sudo iptables -F", check=False)
        self.run_command("sudo iptables -t nat -F", check=False)
        
        # Configure NAT
        nat_commands = [
            f"sudo iptables -t nat -A POSTROUTING -o {eth_interface} -j MASQUERADE",
            f"sudo iptables -A FORWARD -i {eth_interface} -o {self.wifi_interface} -m state --state RELATED,ESTABLISHED -j ACCEPT",
            f"sudo iptables -A FORWARD -i {self.wifi_interface} -o {eth_interface} -j ACCEPT"
        ]
        
        for cmd in nat_commands:
            self.run_command(cmd)
            
        # Save iptables rules
        self.run_command("sudo iptables-save > /etc/iptables.ipv4.nat", check=False)
        
    def start_ap_services(self):
        """Start AP services"""
        services = ['hostapd', 'dnsmasq']
        
        for service in services:
            self.logger.info(f"Starting {service}")
            stdout, stderr = self.run_command(f"sudo systemctl start {service}")
            
            if stderr:
                self.logger.error(f"Failed to start {service}: {stderr}")
                return False
                
            # Enable service to start on boot
            self.run_command(f"sudo systemctl enable {service}", check=False)
            
        self.logger.info("AP mode enabled successfully")
        return True
        
    def disable_ap_mode(self):
        """Disable AP mode and return to normal WiFi"""
        self.logger.info("Disabling AP mode...")
        
        # Stop AP services
        services = ['hostapd', 'dnsmasq']
        for service in services:
            self.run_command(f"sudo systemctl stop {service}", check=False)
            self.run_command(f"sudo systemctl disable {service}", check=False)
            
        # Clear iptables rules
        self.run_command("sudo iptables -F", check=False)
        self.run_command("sudo iptables -t nat -F", check=False)
        
        # Reset WiFi interface
        self.run_command(f"sudo ip addr flush dev {self.wifi_interface}", check=False)
        self.run_command(f"sudo ip link set {self.wifi_interface} down", check=False)
        self.run_command(f"sudo ip link set {self.wifi_interface} up", check=False)
        
        # Restart network manager or dhcpcd
        self.run_command("sudo systemctl restart dhcpcd", check=False)
        
        self.logger.info("AP mode disabled successfully")
        return True
        
    def get_ap_status(self):
        """Get current AP status"""
        try:
            # Check if hostapd is running
            hostapd_status = self.run_command("sudo systemctl is-active hostapd", check=False)[0]
            
            # Check if dnsmasq is running
            dnsmasq_status = self.run_command("sudo systemctl is-active dnsmasq", check=False)[0]
            
            # Get connected clients (if AP is active)
            clients = []
            if hostapd_status == "active":
                clients = self.get_connected_clients()
                
            interface_status = self.get_interface_status(self.wifi_interface)
            
            return {
                'ap_enabled': hostapd_status == "active" and dnsmasq_status == "active",
                'hostapd_status': hostapd_status,
                'dnsmasq_status': dnsmasq_status,
                'interface_status': interface_status,
                'connected_clients': clients,
                'ssid': self.ap_config['ssid'] if hostapd_status == "active" else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting AP status: {e}")
            return {'error': str(e)}
            
    def get_connected_clients(self):
        """Get list of connected AP clients"""
        clients = []
        try:
            # Parse DHCP leases
            lease_file = "/var/lib/dhcp/dhcpcd.leases"
            if os.path.exists(lease_file):
                with open(lease_file, 'r') as f:
                    # Parse DHCP lease file for connected clients
                    pass
                    
            # Alternative: parse ARP table
            arp_output, _ = self.run_command("arp -a", check=False)
            if arp_output:
                for line in arp_output.split('\n'):
                    if self.ap_config['ip_range'].split('/')[0][:-1] in line:
                        # Extract client info from ARP table
                        parts = line.split()
                        if len(parts) >= 4:
                            clients.append({
                                'ip': parts[1].strip('()'),
                                'mac': parts[3],
                                'interface': parts[5] if len(parts) > 5 else 'unknown'
                            })
                            
        except Exception as e:
            self.logger.error(f"Error getting connected clients: {e}")
            
        return clients

def main():
    parser = argparse.ArgumentParser(description='Radxa Rock5B+ Access Point Manager')
    parser.add_argument('--enable-ap', action='store_true', help='Enable AP mode')
    parser.add_argument('--disable-ap', action='store_true', help='Disable AP mode')
    parser.add_argument('--status', action='store_true', help='Show AP status')
    parser.add_argument('--config', default=str(CONFIG_PATH), 
                        help='Path to configuration file')
    args = parser.parse_args()
    
    ap_manager = APManager(args.config)
    
    if args.enable_ap:
        success = ap_manager.enable_ap_mode()
        sys.exit(0 if success else 1)
    elif args.disable_ap:
        success = ap_manager.disable_ap_mode()
        sys.exit(0 if success else 1)
    elif args.status:
        status = ap_manager.get_ap_status()
        print(yaml.dump(status, default_flow_style=False))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
