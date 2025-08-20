#!/usr/bin/env python3
"""
Bandwidth Calculator for CCTV and Video Streaming
Calculate raw and compressed video bandwidth requirements
"""

import argparse
import json
import yaml
import math
from datetime import datetime

class BandwidthCalculator:
    def __init__(self):
        self.common_resolutions = {
            'qvga': (320, 240),
            'vga': (640, 480),
            'svga': (800, 600),
            '720p': (1280, 720),
            '1080p': (1920, 1080),
            '1440p': (2560, 1440),
            '4k': (3840, 2160),
            '8k': (7680, 4320)
        }
        
        self.compression_ratios = {
            'raw': 1.0,
            'mjpeg': 0.1,  # 10:1 compression
            'h264_low': 0.02,  # 50:1 compression
            'h264_medium': 0.015,  # 67:1 compression
            'h264_high': 0.01,  # 100:1 compression
            'h265_low': 0.015,  # 67:1 compression
            'h265_medium': 0.01,  # 100:1 compression
            'h265_high': 0.005,  # 200:1 compression
        }
        
    def calculate_raw_bandwidth(self, width, height, fps, bit_depth=8, channels=3):
        """
        Calculate raw video bandwidth requirements
        
        Args:
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            bit_depth: Bits per channel (usually 8)
            channels: Color channels (3 for RGB, 1 for grayscale)
            
        Returns:
            Dictionary with bandwidth calculations
        """
        # Calculate bits per pixel
        bits_per_pixel = bit_depth * channels
        
        # Calculate bits per frame
        bits_per_frame = width * height * bits_per_pixel
        
        # Calculate bits per second
        bits_per_second = bits_per_frame * fps
        
        # Convert to various units
        bytes_per_second = bits_per_second / 8
        kbps = bits_per_second / 1000
        mbps = bits_per_second / (1000 * 1000)
        gbps = bits_per_second / (1000 * 1000 * 1000)
        
        # Storage calculations (per hour, per day)
        bytes_per_hour = bytes_per_second * 3600
        bytes_per_day = bytes_per_hour * 24
        
        gb_per_hour = bytes_per_hour / (1024 * 1024 * 1024)
        gb_per_day = bytes_per_day / (1024 * 1024 * 1024)
        tb_per_day = gb_per_day / 1024
        
        return {
            'resolution': f"{width}x{height}",
            'fps': fps,
            'bit_depth': bit_depth,
            'channels': channels,
            'bits_per_pixel': bits_per_pixel,
            'bits_per_frame': bits_per_frame,
            'bandwidth': {
                'bits_per_second': bits_per_second,
                'bytes_per_second': bytes_per_second,
                'kbps': round(kbps, 2),
                'mbps': round(mbps, 2),
                'gbps': round(gbps, 4)
            },
            'storage': {
                'bytes_per_hour': bytes_per_hour,
                'bytes_per_day': bytes_per_day,
                'gb_per_hour': round(gb_per_hour, 2),
                'gb_per_day': round(gb_per_day, 2),
                'tb_per_day': round(tb_per_day, 4)
            }
        }
        
    def calculate_compressed_bandwidth(self, raw_bandwidth, compression_type='h264_medium'):
        """
        Calculate compressed video bandwidth
        
        Args:
            raw_bandwidth: Raw bandwidth calculation result
            compression_type: Type of compression to apply
            
        Returns:
            Dictionary with compressed bandwidth calculations
        """
        if compression_type not in self.compression_ratios:
            raise ValueError(f"Unknown compression type: {compression_type}")
            
        ratio = self.compression_ratios[compression_type]
        
        compressed = {
            'compression_type': compression_type,
            'compression_ratio': f"{1/ratio:.0f}:1",
            'compression_factor': ratio,
            'bandwidth': {},
            'storage': {}
        }
        
        # Apply compression to bandwidth
        for key, value in raw_bandwidth['bandwidth'].items():
            if isinstance(value, (int, float)):
                compressed['bandwidth'][key] = round(value * ratio, 4)
            else:
                compressed['bandwidth'][key] = value
                
        # Apply compression to storage
        for key, value in raw_bandwidth['storage'].items():
            if isinstance(value, (int, float)):
                compressed['storage'][key] = round(value * ratio, 4)
            else:
                compressed['storage'][key] = value
                
        return compressed
        
    def get_resolution_specs(self, resolution_name):
        """Get width and height for common resolution names"""
        resolution_name = resolution_name.lower()
        if resolution_name in self.common_resolutions:
            return self.common_resolutions[resolution_name]
        else:
            raise ValueError(f"Unknown resolution: {resolution_name}")
            
    def calculate_multiple_streams(self, streams):
        """
        Calculate bandwidth for multiple camera streams
        
        Args:
            streams: List of stream configurations
            
        Returns:
            Dictionary with total bandwidth calculations
        """
        total_bandwidth = {
            'bits_per_second': 0,
            'mbps': 0,
            'gb_per_day': 0
        }
        
        stream_details = []
        
        for i, stream in enumerate(streams):
            # Parse resolution
            if 'resolution' in stream:
                if stream['resolution'] in self.common_resolutions:
                    width, height = self.common_resolutions[stream['resolution']]
                else:
                    # Try to parse WxH format
                    try:
                        width, height = map(int, stream['resolution'].split('x'))
                    except:
                        raise ValueError(f"Invalid resolution format: {stream['resolution']}")
            else:
                width = stream['width']
                height = stream['height']
            
            # Calculate raw bandwidth
            raw = self.calculate_raw_bandwidth(
                width, 
                height, 
                stream['fps'],
                stream.get('bit_depth', 8),
                stream.get('channels', 3)
            )
            
            # Calculate compressed bandwidth if specified
            if 'compression' in stream:
                compressed = self.calculate_compressed_bandwidth(raw, stream['compression'])
                bandwidth_to_use = compressed
            else:
                bandwidth_to_use = raw
                
            # Add to totals
            total_bandwidth['bits_per_second'] += bandwidth_to_use['bandwidth']['bits_per_second']
            total_bandwidth['mbps'] += bandwidth_to_use['bandwidth']['mbps']
            total_bandwidth['gb_per_day'] += bandwidth_to_use['storage']['gb_per_day']
            
            stream_details.append({
                'stream_id': i + 1,
                'name': stream.get('name', f'Stream {i + 1}'),
                'resolution': f"{width}x{height}",
                'fps': stream['fps'],
                'compression': stream.get('compression', 'raw'),
                'bandwidth_mbps': bandwidth_to_use['bandwidth']['mbps'],
                'storage_gb_per_day': bandwidth_to_use['storage']['gb_per_day']
            })
            
        return {
            'total_streams': len(streams),
            'total_bandwidth': total_bandwidth,
            'streams': stream_details,
            'network_recommendations': self.get_network_recommendations(total_bandwidth['mbps'])
        }
        
    def get_network_recommendations(self, total_mbps):
        """
        Get network infrastructure recommendations based on total bandwidth
        
        Args:
            total_mbps: Total bandwidth in Mbps
            
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            'minimum_network_speed': f"{math.ceil(total_mbps * 1.5)} Mbps",  # 50% overhead
            'recommended_network_speed': f"{math.ceil(total_mbps * 2)} Mbps",  # 100% overhead
        }
        
        # Network type recommendations
        if total_mbps <= 10:
            recommendations['network_type'] = '10 Mbps Ethernet (sufficient)'
            recommendations['wifi'] = '802.11n (2.4GHz) sufficient'
        elif total_mbps <= 100:
            recommendations['network_type'] = '100 Mbps Ethernet (Fast Ethernet)'
            recommendations['wifi'] = '802.11n (5GHz) or 802.11ac recommended'
        elif total_mbps <= 1000:
            recommendations['network_type'] = '1 Gbps Ethernet (Gigabit)'
            recommendations['wifi'] = '802.11ac or 802.11ax (WiFi 6) required'
        else:
            recommendations['network_type'] = '10 Gbps Ethernet or higher'
            recommendations['wifi'] = '802.11ax (WiFi 6) with multiple streams'
            
        # Storage recommendations
        gb_per_day = total_mbps * 0.0108  # Approximate conversion
        if gb_per_day <= 100:
            recommendations['storage'] = 'Standard HDD sufficient'
        elif gb_per_day <= 1000:
            recommendations['storage'] = 'Multiple HDDs or RAID recommended'
        else:
            recommendations['storage'] = 'High-capacity NAS or enterprise storage required'
            
        return recommendations
        
    def create_bandwidth_report(self, configurations):
        """
        Create a comprehensive bandwidth report
        
        Args:
            configurations: List of video configurations to analyze
            
        Returns:
            Dictionary with complete bandwidth analysis
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'configurations': [],
            'summary': {
                'total_configurations': len(configurations),
                'bandwidth_range_mbps': [float('inf'), 0],
                'storage_range_gb_per_day': [float('inf'), 0]
            }
        }
        
        for config in configurations:
            # Parse resolution
            if 'resolution' in config:
                if config['resolution'] in self.common_resolutions:
                    width, height = self.common_resolutions[config['resolution']]
                else:
                    # Try to parse WxH format
                    try:
                        width, height = map(int, config['resolution'].split('x'))
                    except:
                        raise ValueError(f"Invalid resolution format: {config['resolution']}")
            else:
                width = config['width']
                height = config['height']
                
            # Calculate raw bandwidth
            raw = self.calculate_raw_bandwidth(
                width, height, config['fps'],
                config.get('bit_depth', 8),
                config.get('channels', 3)
            )
            
            config_result = {
                'name': config.get('name', f"{width}x{height}@{config['fps']}fps"),
                'raw_bandwidth': raw
            }
            
            # Calculate compressed versions
            compressions = config.get('compressions', ['h264_medium'])
            config_result['compressed_options'] = []
            
            for comp in compressions:
                compressed = self.calculate_compressed_bandwidth(raw, comp)
                config_result['compressed_options'].append(compressed)
                
                # Update summary ranges
                mbps = compressed['bandwidth']['mbps']
                gb_per_day = compressed['storage']['gb_per_day']
                
                if mbps < report['summary']['bandwidth_range_mbps'][0]:
                    report['summary']['bandwidth_range_mbps'][0] = mbps
                if mbps > report['summary']['bandwidth_range_mbps'][1]:
                    report['summary']['bandwidth_range_mbps'][1] = mbps
                    
                if gb_per_day < report['summary']['storage_range_gb_per_day'][0]:
                    report['summary']['storage_range_gb_per_day'][0] = gb_per_day
                if gb_per_day > report['summary']['storage_range_gb_per_day'][1]:
                    report['summary']['storage_range_gb_per_day'][1] = gb_per_day
                    
            report['configurations'].append(config_result)
            
        return report

def main():
    parser = argparse.ArgumentParser(description='CCTV Bandwidth Calculator')
    parser.add_argument('--resolution', help='Resolution (e.g., 1080p, 1920x1080)')
    parser.add_argument('--width', type=int, help='Video width in pixels')
    parser.add_argument('--height', type=int, help='Video height in pixels')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    parser.add_argument('--bit-depth', type=int, default=8, help='Bits per channel')
    parser.add_argument('--channels', type=int, default=3, help='Color channels (3=RGB, 1=grayscale)')
    parser.add_argument('--compression', help='Compression type (raw, h264_medium, etc.)')
    parser.add_argument('--config-file', help='YAML configuration file for multiple streams')
    parser.add_argument('--list-resolutions', action='store_true', help='List common resolutions')
    parser.add_argument('--list-compressions', action='store_true', help='List compression types')
    parser.add_argument('--output', help='Output file for results (JSON format)')
    
    args = parser.parse_args()
    
    calc = BandwidthCalculator()
    
    if args.list_resolutions:
        print("Common video resolutions:")
        for name, (w, h) in calc.common_resolutions.items():
            print(f"  {name}: {w}x{h}")
        return
        
    if args.list_compressions:
        print("Available compression types:")
        for comp, ratio in calc.compression_ratios.items():
            print(f"  {comp}: {1/ratio:.0f}:1 compression ratio")
        return
        
    if args.config_file:
        # Load configuration from file
        with open(args.config_file, 'r') as f:
            config = yaml.safe_load(f)
            
        if 'streams' in config:
            result = calc.calculate_multiple_streams(config['streams'])
        elif 'configurations' in config:
            result = calc.create_bandwidth_report(config['configurations'])
        else:
            print("Invalid configuration file format")
            return
    else:
        # Single calculation
        if args.resolution:
            try:
                width, height = calc.get_resolution_specs(args.resolution)
            except ValueError as e:
                print(f"Error: {e}")
                return
        elif args.width and args.height:
            width, height = args.width, args.height
        else:
            print("Error: Must specify either --resolution or --width and --height")
            return
            
        # Calculate raw bandwidth
        result = calc.calculate_raw_bandwidth(width, height, args.fps, args.bit_depth, args.channels)
        
        # Add compressed calculation if requested
        if args.compression:
            try:
                compressed = calc.calculate_compressed_bandwidth(result, args.compression)
                result['compressed'] = compressed
            except ValueError as e:
                print(f"Error: {e}")
                return
                
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
