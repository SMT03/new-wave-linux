#!/usr/bin/env python3
"""
Network Monitor for Radxa Rock5B+
Real-time network statistics, bandwidth monitoring, and system information
"""

import os
import sys
import time
import json
import argparse
import logging
import threading
from datetime import datetime, timedelta
from collections import deque, defaultdict
import yaml
import psutil
import netifaces
import subprocess
import socket
import re

class NetworkMonitor:
    def __init__(self, config_path="/workspaces/new-wave-linux/config/settings.yaml"):
        self.config = self.load_config(config_path)
        self.logger = self.setup_logging()
        self.interfaces = self.config['monitoring']['interfaces']
        self.update_interval = self.config['monitoring']['network_update_interval']
        self.data_retention = self.config['monitoring']['data_retention']
        
        # Data storage
        self.network_history = defaultdict(lambda: deque(maxlen=3600))  # 1 hour at 1s intervals
        self.bandwidth_history = defaultdict(lambda: deque(maxlen=3600))
        self.system_info = {}
        self.running = False
        self.monitor_thread = None
        
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
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
        
    def get_network_interfaces(self):
        """Get all available network interfaces"""
        interfaces = []
        for interface in netifaces.interfaces():
            if interface != 'lo':  # Skip loopback
                info = self.get_interface_info(interface)
                if info:
                    interfaces.append(info)
        return interfaces
        
    def get_interface_info(self, interface):
        """Get detailed information about a network interface"""
        try:
            # Get interface statistics
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            
            if interface not in stats:
                return None
                
            interface_stats = stats[interface]
            interface_addrs = addrs.get(interface, [])
            
            # Extract IP addresses
            ipv4_addr = None
            ipv6_addr = None
            mac_addr = None
            
            for addr in interface_addrs:
                if addr.family == socket.AF_INET:
                    ipv4_addr = addr.address
                elif addr.family == socket.AF_INET6:
                    ipv6_addr = addr.address
                elif addr.family == psutil.AF_LINK:
                    mac_addr = addr.address
                    
            # Get interface type
            interface_type = self.get_interface_type(interface)
            
            return {
                'name': interface,
                'type': interface_type,
                'is_up': interface_stats.isup,
                'speed': interface_stats.speed,
                'mtu': interface_stats.mtu,
                'ipv4_address': ipv4_addr,
                'ipv6_address': ipv6_addr,
                'mac_address': mac_addr,
                'duplex': interface_stats.duplex.name if interface_stats.duplex else 'unknown'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting interface info for {interface}: {e}")
            return None
            
    def get_interface_type(self, interface):
        """Determine the type of network interface"""
        if interface.startswith('eth'):
            return 'ethernet'
        elif interface.startswith('wlan') or interface.startswith('wifi'):
            return 'wireless'
        elif interface.startswith('usb'):
            return 'usb'
        elif interface.startswith('ppp'):
            return 'ppp'
        else:
            return 'unknown'
            
    def get_network_statistics(self):
        """Get current network I/O statistics"""
        try:
            # Get overall network stats
            net_io = psutil.net_io_counters()
            net_io_pernic = psutil.net_io_counters(pernic=True)
            
            current_time = datetime.now()
            
            stats = {
                'timestamp': current_time.isoformat(),
                'overall': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                },
                'interfaces': {}
            }
            
            # Get per-interface stats
            for interface in self.interfaces:
                if interface in net_io_pernic:
                    iface_stats = net_io_pernic[interface]
                    stats['interfaces'][interface] = {
                        'bytes_sent': iface_stats.bytes_sent,
                        'bytes_recv': iface_stats.bytes_recv,
                        'packets_sent': iface_stats.packets_sent,
                        'packets_recv': iface_stats.packets_recv,
                        'errin': iface_stats.errin,
                        'errout': iface_stats.errout,
                        'dropin': iface_stats.dropin,
                        'dropout': iface_stats.dropout
                    }
                    
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting network statistics: {e}")
            return None
            
    def calculate_bandwidth(self, current_stats, previous_stats, time_delta):
        """Calculate bandwidth from two statistics snapshots"""
        if not previous_stats or time_delta <= 0:
            return None
            
        bandwidth = {
            'timestamp': current_stats['timestamp'],
            'overall': {},
            'interfaces': {}
        }
        
        # Calculate overall bandwidth
        current_overall = current_stats['overall']
        previous_overall = previous_stats['overall']
        
        bandwidth['overall'] = {
            'bytes_sent_per_sec': (current_overall['bytes_sent'] - previous_overall['bytes_sent']) / time_delta,
            'bytes_recv_per_sec': (current_overall['bytes_recv'] - previous_overall['bytes_recv']) / time_delta,
            'packets_sent_per_sec': (current_overall['packets_sent'] - previous_overall['packets_sent']) / time_delta,
            'packets_recv_per_sec': (current_overall['packets_recv'] - previous_overall['packets_recv']) / time_delta
        }
        
        # Calculate per-interface bandwidth
        for interface in self.interfaces:
            if (interface in current_stats['interfaces'] and 
                interface in previous_stats['interfaces']):
                
                current_iface = current_stats['interfaces'][interface]
                previous_iface = previous_stats['interfaces'][interface]
                
                bandwidth['interfaces'][interface] = {
                    'bytes_sent_per_sec': (current_iface['bytes_sent'] - previous_iface['bytes_sent']) / time_delta,
                    'bytes_recv_per_sec': (current_iface['bytes_recv'] - previous_iface['bytes_recv']) / time_delta,
                    'packets_sent_per_sec': (current_iface['packets_sent'] - previous_iface['packets_sent']) / time_delta,
                    'packets_recv_per_sec': (current_iface['packets_recv'] - previous_iface['packets_recv']) / time_delta,
                    'mbps_sent': ((current_iface['bytes_sent'] - previous_iface['bytes_sent']) * 8) / (time_delta * 1024 * 1024),
                    'mbps_recv': ((current_iface['bytes_recv'] - previous_iface['bytes_recv']) * 8) / (time_delta * 1024 * 1024)
                }
                
        return bandwidth
        
    def get_system_info(self):
        """Get system information"""
        try:
            # CPU information
            cpu_info = {
                'count': psutil.cpu_count(),
                'usage_percent': psutil.cpu_percent(interval=1),
                'per_cpu': psutil.cpu_percent(interval=1, percpu=True),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free
            }
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_info = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            }
            
            # Load average
            load_avg = os.getloadavg()
            
            # Uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'load_average': {
                    '1min': load_avg[0],
                    '5min': load_avg[1],
                    '15min': load_avg[2]
                },
                'uptime_seconds': uptime
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return None
            
    def get_network_connections(self):
        """Get active network connections"""
        try:
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                connection_info = {
                    'fd': conn.fd,
                    'family': conn.family.name if conn.family else 'unknown',
                    'type': conn.type.name if conn.type else 'unknown',
                    'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    'status': conn.status,
                    'pid': conn.pid
                }
                
                # Get process name if PID is available
                if conn.pid:
                    try:
                        process = psutil.Process(conn.pid)
                        connection_info['process_name'] = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        connection_info['process_name'] = 'unknown'
                        
                connections.append(connection_info)
                
            return connections
            
        except Exception as e:
            self.logger.error(f"Error getting network connections: {e}")
            return []
            
    def get_dhcp_leases(self):
        """Get DHCP leases information"""
        leases = []
        lease_files = [
            '/var/lib/dhcp/dhcpd.leases',
            '/var/lib/dhcpcd5/dhcpcd.leases',
            '/var/lib/NetworkManager/dhcpcd.leases'
        ]
        
        for lease_file in lease_files:
            if os.path.exists(lease_file):
                try:
                    with open(lease_file, 'r') as f:
                        content = f.read()
                        # Parse DHCP lease file
                        # This is a simplified parser
                        for line in content.split('\n'):
                            if 'lease' in line and '{' in line:
                                ip = line.split()[1]
                                leases.append({'ip': ip, 'file': lease_file})
                except Exception as e:
                    self.logger.error(f"Error reading lease file {lease_file}: {e}")
                    
        return leases
        
    def get_dns_servers(self):
        """Get configured DNS servers"""
        dns_servers = []
        
        try:
            # Try to read from resolv.conf
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.startswith('nameserver'):
                        dns_ip = line.split()[1]
                        dns_servers.append(dns_ip)
                        
        except Exception as e:
            self.logger.error(f"Error reading DNS servers: {e}")
            
        return dns_servers
        
    def get_routing_table(self):
        """Get system routing table"""
        try:
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            routes = []
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    routes.append(line.strip())
                    
            return routes
            
        except Exception as e:
            self.logger.error(f"Error getting routing table: {e}")
            return []
            
    def start_monitoring(self):
        """Start continuous network monitoring"""
        if self.running:
            self.logger.warning("Monitoring already running")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("Network monitoring started")
        
    def stop_monitoring(self):
        """Stop network monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Network monitoring stopped")
        
    def _monitoring_loop(self):
        """Main monitoring loop"""
        previous_stats = None
        previous_time = None
        
        while self.running:
            try:
                current_time = datetime.now()
                current_stats = self.get_network_statistics()
                
                if current_stats:
                    # Store network statistics
                    for interface in self.interfaces:
                        if interface in current_stats['interfaces']:
                            self.network_history[interface].append({
                                'timestamp': current_time,
                                'stats': current_stats['interfaces'][interface]
                            })
                            
                    # Calculate and store bandwidth
                    if previous_stats and previous_time:
                        time_delta = (current_time - previous_time).total_seconds()
                        bandwidth = self.calculate_bandwidth(current_stats, previous_stats, time_delta)
                        
                        if bandwidth:
                            for interface in self.interfaces:
                                if interface in bandwidth['interfaces']:
                                    self.bandwidth_history[interface].append({
                                        'timestamp': current_time,
                                        'bandwidth': bandwidth['interfaces'][interface]
                                    })
                                    
                    previous_stats = current_stats
                    previous_time = current_time
                    
                # Update system info less frequently
                if int(current_time.timestamp()) % self.config['monitoring']['system_update_interval'] == 0:
                    self.system_info = self.get_system_info()
                    
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.update_interval)
                
    def get_current_status(self):
        """Get current comprehensive network status"""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'interfaces': self.get_network_interfaces(),
                'network_stats': self.get_network_statistics(),
                'system_info': self.system_info,
                'connections': self.get_network_connections(),
                'dhcp_leases': self.get_dhcp_leases(),
                'dns_servers': self.get_dns_servers(),
                'routing_table': self.get_routing_table(),
                'monitoring_active': self.running
            }
        except Exception as e:
            self.logger.error(f"Error getting current status: {e}")
            return {'error': str(e)}
            
    def get_bandwidth_history(self, interface, duration_minutes=60):
        """Get bandwidth history for specified interface"""
        if interface not in self.bandwidth_history:
            return []
            
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        history = []
        
        for entry in self.bandwidth_history[interface]:
            if entry['timestamp'] > cutoff_time:
                history.append(entry)
                
        return history
        
    def export_data(self, filename=None):
        """Export monitoring data to JSON file"""
        if not filename:
            filename = f"network_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        data = {
            'export_time': datetime.now().isoformat(),
            'network_history': {k: list(v) for k, v in self.network_history.items()},
            'bandwidth_history': {k: list(v) for k, v in self.bandwidth_history.items()},
            'system_info': self.system_info,
            'current_status': self.get_current_status()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info(f"Data exported to {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Radxa Rock5B+ Network Monitor')
    parser.add_argument('--interface', help='Specific interface to monitor')
    parser.add_argument('--duration', type=int, default=60, help='Monitoring duration in seconds')
    parser.add_argument('--export', help='Export data to file')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--config', default='/workspaces/new-wave-linux/config/settings.yaml',
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    monitor = NetworkMonitor(args.config)
    
    if args.interface:
        monitor.interfaces = [args.interface]
        
    if args.status:
        status = monitor.get_current_status()
        print(json.dumps(status, indent=2, default=str))
    elif args.continuous:
        try:
            monitor.start_monitoring()
            print("Monitoring started. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\nMonitoring stopped.")
    else:
        # Run for specified duration
        monitor.start_monitoring()
        time.sleep(args.duration)
        monitor.stop_monitoring()
        
        if args.export:
            monitor.export_data(args.export)

if __name__ == "__main__":
    main()
