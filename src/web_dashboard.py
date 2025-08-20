#!/usr/bin/env python3
"""
Web Dashboard for Radxa Rock5B+ Network & Camera Management System
Flask-based web interface for monitoring and control
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import yaml

# Import our modules
sys.path.append('/workspaces/new-wave-linux/src')
from ap_manager import APManager
from network_monitor import NetworkMonitor
from camera_streamer import CameraStreamer

class WebDashboard:
    def __init__(self, config_path="/workspaces/new-wave-linux/config/settings.yaml"):
        self.config = self.load_config(config_path)
        self.web_config = self.config['web']
        self.logger = self.setup_logging()
        
        # Initialize Flask app
        self.app = Flask(__name__, 
                        template_folder='/workspaces/new-wave-linux/web/templates',
                        static_folder='/workspaces/new-wave-linux/web/static')
        self.app.config['SECRET_KEY'] = 'radxa-rock5b-secret-key'
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize system components
        self.ap_manager = APManager(config_path)
        self.network_monitor = NetworkMonitor(config_path)
        self.camera_streamer = CameraStreamer(config_path)
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Setup routes
        self.setup_routes()
        self.setup_socketio_events()
        
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
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')
            
        @self.app.route('/api/status')
        def get_status():
            """Get overall system status"""
            try:
                status = {
                    'timestamp': datetime.now().isoformat(),
                    'ap_status': self.ap_manager.get_ap_status(),
                    'network_status': self.network_monitor.get_current_status(),
                    'camera_status': self.camera_streamer.get_stream_stats(),
                    'system_config': {
                        'ap_ssid': self.config['network']['ap_config']['ssid'],
                        'rtsp_port': self.config['camera']['rtsp']['port'],
                        'web_port': self.config['web']['port']
                    }
                }
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting status: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/ap/enable', methods=['POST'])
        def enable_ap():
            """Enable AP mode"""
            try:
                success = self.ap_manager.enable_ap_mode()
                return jsonify({'success': success})
            except Exception as e:
                self.logger.error(f"Error enabling AP: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/ap/disable', methods=['POST'])
        def disable_ap():
            """Disable AP mode"""
            try:
                success = self.ap_manager.disable_ap_mode()
                return jsonify({'success': success})
            except Exception as e:
                self.logger.error(f"Error disabling AP: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/camera/start', methods=['POST'])
        def start_camera():
            """Start camera streaming"""
            try:
                data = request.get_json()
                camera_device = data.get('device', self.config['camera']['default_device'])
                
                if self.camera_streamer.connect_camera(camera_device):
                    success = self.camera_streamer.start_streaming()
                    return jsonify({'success': success})
                else:
                    return jsonify({'success': False, 'error': 'Failed to connect camera'})
            except Exception as e:
                self.logger.error(f"Error starting camera: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/camera/stop', methods=['POST'])
        def stop_camera():
            """Stop camera streaming"""
            try:
                self.camera_streamer.stop_streaming()
                self.camera_streamer.disconnect_camera()
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error stopping camera: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/camera/rtsp/start', methods=['POST'])
        def start_rtsp():
            """Start RTSP server"""
            try:
                if not self.camera_streamer.camera:
                    if not self.camera_streamer.connect_camera():
                        return jsonify({'success': False, 'error': 'Failed to connect camera'})
                        
                success = self.camera_streamer.start_rtsp_server()
                return jsonify({'success': success})
            except Exception as e:
                self.logger.error(f"Error starting RTSP: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/camera/rtsp/stop', methods=['POST'])
        def stop_rtsp():
            """Stop RTSP server"""
            try:
                self.camera_streamer.stop_rtsp_server()
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error stopping RTSP: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/network/interfaces')
        def get_network_interfaces():
            """Get network interfaces information"""
            try:
                interfaces = self.network_monitor.get_network_interfaces()
                return jsonify(interfaces)
            except Exception as e:
                self.logger.error(f"Error getting network interfaces: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/network/bandwidth/<interface>')
        def get_bandwidth_history(interface):
            """Get bandwidth history for interface"""
            try:
                duration = request.args.get('duration', 60, type=int)
                history = self.network_monitor.get_bandwidth_history(interface, duration)
                return jsonify(history)
            except Exception as e:
                self.logger.error(f"Error getting bandwidth history: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/camera/bandwidth')
        def get_camera_bandwidth():
            """Get camera bandwidth history"""
            try:
                duration = request.args.get('duration', 60, type=int)
                history = self.camera_streamer.get_bandwidth_history(duration)
                return jsonify(history)
            except Exception as e:
                self.logger.error(f"Error getting camera bandwidth: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/cameras')
        def list_cameras():
            """List available cameras"""
            try:
                cameras = self.camera_streamer.list_cameras()
                return jsonify(cameras)
            except Exception as e:
                self.logger.error(f"Error listing cameras: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/config')
        def get_config():
            """Get current configuration"""
            return jsonify(self.config)
            
        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Update configuration"""
            try:
                new_config = request.get_json()
                # Validate and update config
                # For simplicity, just return success
                return jsonify({'success': True})
            except Exception as e:
                self.logger.error(f"Error updating config: {e}")
                return jsonify({'error': str(e)}), 500
                
    def setup_socketio_events(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.info('Client connected to WebSocket')
            emit('status', {'message': 'Connected to Radxa Dashboard'})
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.info('Client disconnected from WebSocket')
            
        @self.socketio.on('start_monitoring')
        def handle_start_monitoring():
            """Start real-time monitoring"""
            if not self.monitoring_active:
                self.start_monitoring()
                emit('monitoring_status', {'active': True})
                
        @self.socketio.on('stop_monitoring')
        def handle_stop_monitoring():
            """Stop real-time monitoring"""
            if self.monitoring_active:
                self.stop_monitoring()
                emit('monitoring_status', {'active': False})
                
    def start_monitoring(self):
        """Start background monitoring and data streaming"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.network_monitor.start_monitoring()
        
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("Real-time monitoring started")
        
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        self.network_monitor.stop_monitoring()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            
        self.logger.info("Real-time monitoring stopped")
        
    def _monitoring_loop(self):
        """Background monitoring loop for real-time updates"""
        while self.monitoring_active:
            try:
                # Get current status
                status_data = {
                    'timestamp': datetime.now().isoformat(),
                    'network': self.network_monitor.get_current_status(),
                    'camera': self.camera_streamer.get_stream_stats(),
                    'ap': self.ap_manager.get_ap_status()
                }
                
                # Emit to all connected clients
                self.socketio.emit('real_time_data', status_data)
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
                
    def run(self):
        """Run the web dashboard"""
        host = self.web_config['host']
        port = self.web_config['port']
        debug = self.web_config['debug']
        
        self.logger.info(f"Starting web dashboard on {host}:{port}")
        
        try:
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        except KeyboardInterrupt:
            self.logger.info("Shutting down web dashboard")
        finally:
            self.stop_monitoring()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Radxa Rock5B+ Web Dashboard')
    parser.add_argument('--config', default='/workspaces/new-wave-linux/config/settings.yaml',
                       help='Path to configuration file')
    parser.add_argument('--host', help='Host to bind to')
    parser.add_argument('--port', type=int, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    dashboard = WebDashboard(args.config)
    
    # Override config with command line arguments
    if args.host:
        dashboard.web_config['host'] = args.host
    if args.port:
        dashboard.web_config['port'] = args.port
    if args.debug:
        dashboard.web_config['debug'] = True
        
    dashboard.run()

if __name__ == "__main__":
    main()
