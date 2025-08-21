#!/usr/bin/env python3
"""
Camera Streamer for Radxa Rock5B+
RTSP streaming with frame rate monitoring and bandwidth analysis
"""

import os
import sys
import time
import json
import argparse
import logging
import threading
import subprocess
from datetime import datetime, timedelta
from collections import deque
import yaml
import cv2
import numpy as np
import psutil
from pathlib import Path

# Auto-detect config path
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "settings.yaml"

class CameraStreamer:
    """
    Camera streaming and recording system for Radxa Rock5B+
    """
    
    def __init__(self, config_path=None):
        """
        Initialize Camera Streamer
        
        Args:
            config_path: Path to configuration file (auto-detected if None)
        """
        if config_path is None:
            config_path = str(CONFIG_PATH)
        self.config = self.load_config(config_path)
        self.camera_config = self.config['camera']
        self.logger = self.setup_logging()
        
        # Camera and streaming state
        self.camera = None
        self.streaming = False
        self.recording = False
        self.stream_thread = None
        self.rtsp_process = None
        
        # Performance monitoring
        self.frame_count = 0
        self.start_time = None
        self.frame_times = deque(maxlen=100)  # Last 100 frame timestamps
        self.frame_sizes = deque(maxlen=100)  # Last 100 frame sizes
        self.dropped_frames = 0
        self.bandwidth_history = deque(maxlen=3600)  # 1 hour of bandwidth data
        
        # Statistics
        self.stats = {
            'stream_active': False,
            'camera_connected': False,
            'current_fps': 0,
            'target_fps': self.camera_config['video']['fps'],
            'resolution': f"{self.camera_config['video']['width']}x{self.camera_config['video']['height']}",
            'dropped_frames': 0,
            'total_frames': 0,
            'bandwidth_mbps': 0,
            'raw_bandwidth_mbps': 0
        }
        
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
        
    def list_cameras(self):
        """List available camera devices"""
        cameras = []
        
        # Check V4L2 devices
        for i in range(10):  # Check first 10 video devices
            device_path = f"/dev/video{i}"
            if os.path.exists(device_path):
                try:
                    # Try to open the device to check if it's a valid camera
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        # Get camera info
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        camera_info = {
                            'device': device_path,
                            'index': i,
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'type': 'V4L2'
                        }
                        cameras.append(camera_info)
                        cap.release()
                except Exception as e:
                    self.logger.debug(f"Failed to query camera {device_path}: {e}")
                    
        # Check for USB cameras using lsusb
        try:
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            usb_devices = result.stdout
            
            # Look for common camera device keywords
            camera_keywords = ['camera', 'webcam', 'video', 'imaging']
            for line in usb_devices.split('\n'):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in camera_keywords):
                    cameras.append({
                        'device': 'USB',
                        'description': line.strip(),
                        'type': 'USB'
                    })
        except Exception as e:
            self.logger.debug(f"Failed to list USB devices: {e}")
            
        return cameras
        
    def connect_camera(self, device_path=None):
        """Connect to camera device"""
        if device_path is None:
            device_path = self.camera_config['default_device']
            
        try:
            # Try to open camera
            if device_path.startswith('/dev/video'):
                # Extract device index
                device_index = int(device_path.split('video')[1])
                self.camera = cv2.VideoCapture(device_index)
            else:
                # Try as IP camera or other source
                self.camera = cv2.VideoCapture(device_path)
                
            if not self.camera.isOpened():
                self.logger.error(f"Failed to open camera: {device_path}")
                return False
                
            # Configure camera
            self.configure_camera()
            
            self.stats['camera_connected'] = True
            self.logger.info(f"Camera connected: {device_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to camera {device_path}: {e}")
            return False
            
    def configure_camera(self):
        """Configure camera parameters"""
        if not self.camera:
            return False
            
        try:
            video_config = self.camera_config['video']
            
            # Set resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, video_config['width'])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, video_config['height'])
            
            # Set FPS
            self.camera.set(cv2.CAP_PROP_FPS, video_config['fps'])
            
            # Set buffer size to reduce latency
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Verify settings
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"Camera configured: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            # Update stats
            self.stats['resolution'] = f"{actual_width}x{actual_height}"
            self.stats['target_fps'] = actual_fps
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring camera: {e}")
            return False
            
    def disconnect_camera(self):
        """Disconnect camera"""
        if self.camera:
            self.camera.release()
            self.camera = None
            self.stats['camera_connected'] = False
            self.logger.info("Camera disconnected")
            
    def start_rtsp_server(self, port=None):
        """Start RTSP server using FFmpeg"""
        if port is None:
            port = self.camera_config['rtsp']['port']
            
        rtsp_path = self.camera_config['rtsp']['path']
        video_config = self.camera_config['video']
        
        # FFmpeg command for RTSP server
        cmd = [
            'ffmpeg',
            '-f', 'v4l2',
            '-video_size', f"{video_config['width']}x{video_config['height']}",
            '-framerate', str(video_config['fps']),
            '-i', self.camera_config['default_device'],
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-b:v', video_config['bitrate'],
            '-f', 'rtsp',
            f'rtsp://0.0.0.0:{port}{rtsp_path}'
        ]
        
        try:
            self.logger.info(f"Starting RTSP server on port {port}")
            self.rtsp_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Give the server time to start
            time.sleep(2)
            
            if self.rtsp_process.poll() is None:
                self.logger.info(f"RTSP server started: rtsp://<ip>:{port}{rtsp_path}")
                return True
            else:
                stderr = self.rtsp_process.stderr.read()
                self.logger.error(f"RTSP server failed to start: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting RTSP server: {e}")
            return False
            
    def stop_rtsp_server(self):
        """Stop RTSP server"""
        if self.rtsp_process:
            self.rtsp_process.terminate()
            self.rtsp_process.wait(timeout=5)
            self.rtsp_process = None
            self.logger.info("RTSP server stopped")
            
    def calculate_raw_bandwidth(self, width, height, fps, bit_depth=8, channels=3):
        """Calculate raw video bandwidth requirements"""
        bits_per_pixel = bit_depth * channels
        bits_per_frame = width * height * bits_per_pixel
        bits_per_second = bits_per_frame * fps
        mbps = bits_per_second / (1024 * 1024)  # Convert to Mbps
        return mbps
        
    def analyze_frame(self, frame):
        """Analyze frame for quality and statistics"""
        if frame is None:
            return None
            
        current_time = time.time()
        frame_size = frame.nbytes
        
        # Store frame timing and size
        self.frame_times.append(current_time)
        self.frame_sizes.append(frame_size)
        
        # Calculate current FPS
        if len(self.frame_times) >= 2:
            time_window = self.frame_times[-1] - self.frame_times[0]
            if time_window > 0:
                current_fps = (len(self.frame_times) - 1) / time_window
                self.stats['current_fps'] = round(current_fps, 2)
                
        # Calculate bandwidth
        if len(self.frame_sizes) >= 10:  # Use last 10 frames for bandwidth calculation
            avg_frame_size = sum(list(self.frame_sizes)[-10:]) / 10
            if self.stats['current_fps'] > 0:
                bandwidth_bytes_per_sec = avg_frame_size * self.stats['current_fps']
                bandwidth_mbps = (bandwidth_bytes_per_sec * 8) / (1024 * 1024)
                self.stats['bandwidth_mbps'] = round(bandwidth_mbps, 3)
                
        # Calculate raw bandwidth
        height, width = frame.shape[:2]
        raw_bandwidth = self.calculate_raw_bandwidth(width, height, self.stats['current_fps'])
        self.stats['raw_bandwidth_mbps'] = round(raw_bandwidth, 3)
        
        # Frame analysis
        analysis = {
            'timestamp': current_time,
            'frame_size_bytes': frame_size,
            'resolution': f"{width}x{height}",
            'channels': len(frame.shape) if len(frame.shape) > 2 else 1,
            'mean_brightness': np.mean(frame) if len(frame.shape) == 3 else np.mean(frame),
            'frame_number': self.frame_count
        }
        
        # Check for motion (simple method)
        if hasattr(self, 'previous_frame') and self.previous_frame is not None:
            diff = cv2.absdiff(frame, self.previous_frame)
            motion_score = np.mean(diff)
            analysis['motion_score'] = motion_score
            
        self.previous_frame = frame.copy()
        
        return analysis
        
    def start_streaming(self, display=False):
        """Start camera streaming with monitoring"""
        if not self.camera or not self.camera.isOpened():
            self.logger.error("Camera not connected")
            return False
            
        if self.streaming:
            self.logger.warning("Streaming already active")
            return True
            
        self.streaming = True
        self.start_time = time.time()
        self.frame_count = 0
        self.dropped_frames = 0
        
        self.stats['stream_active'] = True
        self.stats['total_frames'] = 0
        self.stats['dropped_frames'] = 0
        
        # Start monitoring thread
        self.stream_thread = threading.Thread(target=self._streaming_loop, args=(display,))
        self.stream_thread.daemon = True
        self.stream_thread.start()
        
        self.logger.info("Camera streaming started")
        return True
        
    def stop_streaming(self):
        """Stop camera streaming"""
        self.streaming = False
        
        if self.stream_thread:
            self.stream_thread.join(timeout=5)
            
        self.stats['stream_active'] = False
        self.logger.info("Camera streaming stopped")
        
    def _streaming_loop(self, display=False):
        """Main streaming loop"""
        target_frame_time = 1.0 / self.stats['target_fps']
        
        while self.streaming:
            try:
                loop_start = time.time()
                
                # Capture frame
                ret, frame = self.camera.read()
                
                if not ret:
                    self.dropped_frames += 1
                    self.stats['dropped_frames'] = self.dropped_frames
                    self.logger.warning("Failed to capture frame")
                    continue
                    
                self.frame_count += 1
                self.stats['total_frames'] = self.frame_count
                
                # Analyze frame
                frame_analysis = self.analyze_frame(frame)
                
                # Store bandwidth data
                if frame_analysis:
                    bandwidth_data = {
                        'timestamp': datetime.now(),
                        'fps': self.stats['current_fps'],
                        'bandwidth_mbps': self.stats['bandwidth_mbps'],
                        'raw_bandwidth_mbps': self.stats['raw_bandwidth_mbps'],
                        'frame_size': frame_analysis['frame_size_bytes']
                    }
                    self.bandwidth_history.append(bandwidth_data)
                    
                # Display frame if requested
                if display:
                    cv2.imshow('Camera Stream', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
                # Frame rate control
                loop_time = time.time() - loop_start
                if loop_time < target_frame_time:
                    time.sleep(target_frame_time - loop_time)
                    
            except Exception as e:
                self.logger.error(f"Error in streaming loop: {e}")
                break
                
        if display:
            cv2.destroyAllWindows()
            
    def get_stream_stats(self):
        """Get current streaming statistics"""
        if self.start_time:
            runtime = time.time() - self.start_time
            avg_fps = self.frame_count / runtime if runtime > 0 else 0
        else:
            runtime = 0
            avg_fps = 0
            
        return {
            'timestamp': datetime.now().isoformat(),
            'camera_connected': self.stats['camera_connected'],
            'stream_active': self.stats['stream_active'],
            'resolution': self.stats['resolution'],
            'target_fps': self.stats['target_fps'],
            'current_fps': self.stats['current_fps'],
            'average_fps': round(avg_fps, 2),
            'total_frames': self.stats['total_frames'],
            'dropped_frames': self.stats['dropped_frames'],
            'drop_rate_percent': round((self.dropped_frames / max(self.frame_count, 1)) * 100, 2),
            'runtime_seconds': round(runtime, 2),
            'bandwidth_mbps': self.stats['bandwidth_mbps'],
            'raw_bandwidth_mbps': self.stats['raw_bandwidth_mbps'],
            'rtsp_active': self.rtsp_process is not None and self.rtsp_process.poll() is None
        }
        
    def get_bandwidth_history(self, duration_minutes=60):
        """Get bandwidth history for specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        history = []
        
        for entry in self.bandwidth_history:
            if entry['timestamp'] > cutoff_time:
                history.append({
                    'timestamp': entry['timestamp'].isoformat(),
                    'fps': entry['fps'],
                    'bandwidth_mbps': entry['bandwidth_mbps'],
                    'raw_bandwidth_mbps': entry['raw_bandwidth_mbps'],
                    'frame_size': entry['frame_size']
                })
                
        return history
        
    def test_camera_performance(self, duration=30):
        """Test camera performance for specified duration"""
        self.logger.info(f"Starting {duration}s camera performance test")
        
        if not self.connect_camera():
            return None
            
        # Start streaming
        self.start_streaming()
        
        # Collect performance data
        test_start = time.time()
        performance_data = []
        
        while time.time() - test_start < duration:
            stats = self.get_stream_stats()
            performance_data.append(stats)
            time.sleep(1)
            
        # Stop streaming
        self.stop_streaming()
        self.disconnect_camera()
        
        # Calculate summary statistics
        if performance_data:
            fps_values = [data['current_fps'] for data in performance_data if data['current_fps'] > 0]
            bandwidth_values = [data['bandwidth_mbps'] for data in performance_data if data['bandwidth_mbps'] > 0]
            
            summary = {
                'test_duration': duration,
                'avg_fps': sum(fps_values) / len(fps_values) if fps_values else 0,
                'min_fps': min(fps_values) if fps_values else 0,
                'max_fps': max(fps_values) if fps_values else 0,
                'avg_bandwidth_mbps': sum(bandwidth_values) / len(bandwidth_values) if bandwidth_values else 0,
                'total_frames': performance_data[-1]['total_frames'],
                'dropped_frames': performance_data[-1]['dropped_frames'],
                'drop_rate_percent': performance_data[-1]['drop_rate_percent'],
                'performance_data': performance_data
            }
            
            self.logger.info(f"Performance test completed: {summary['avg_fps']:.2f} avg FPS, "
                           f"{summary['avg_bandwidth_mbps']:.2f} Mbps avg bandwidth")
            
            return summary
            
        return None

def main():
    parser = argparse.ArgumentParser(description='Radxa Rock5B+ Camera Streamer')
    parser.add_argument('--camera', help='Camera device path (e.g., /dev/video0)')
    parser.add_argument('--list-cameras', action='store_true', help='List available cameras')
    parser.add_argument('--start-rtsp', action='store_true', help='Start RTSP server')
    parser.add_argument('--port', type=int, help='RTSP server port')
    parser.add_argument('--stream', action='store_true', help='Start streaming with display')
    parser.add_argument('--test', type=int, help='Run performance test for N seconds')
    parser.add_argument('--stats', action='store_true', help='Show current statistics')
    parser.add_argument('--config', default=str(CONFIG_PATH),
                        help='Path to configuration file')
    args = parser.parse_args()
    
    streamer = CameraStreamer(args.config)
    
    if args.list_cameras:
        cameras = streamer.list_cameras()
        print("Available cameras:")
        for camera in cameras:
            print(f"  {camera}")
    elif args.test:
        result = streamer.test_camera_performance(args.test)
        if result:
            print(json.dumps(result, indent=2, default=str))
    elif args.start_rtsp:
        if streamer.connect_camera(args.camera):
            success = streamer.start_rtsp_server(args.port)
            if success:
                try:
                    print("RTSP server running. Press Ctrl+C to stop.")
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    streamer.stop_rtsp_server()
                    streamer.disconnect_camera()
    elif args.stream:
        if streamer.connect_camera(args.camera):
            streamer.start_streaming(display=True)
            try:
                print("Streaming started. Press 'q' in the video window or Ctrl+C to stop.")
                while streamer.streaming:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                streamer.stop_streaming()
                streamer.disconnect_camera()
    elif args.stats:
        if streamer.connect_camera(args.camera):
            stats = streamer.get_stream_stats()
            print(json.dumps(stats, indent=2))
            streamer.disconnect_camera()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
