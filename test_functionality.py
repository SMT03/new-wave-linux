#!/usr/bin/env python3
"""
Test functionality for Radxa Rock5B+ system
Tests basic imports and functionality without requiring root privileges
"""

import os
import sys
from pathlib import Path

# Add src directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.append(str(SCRIPT_DIR / "src"))

# Auto-detect config path
CONFIG_PATH = SCRIPT_DIR / "config" / "settings.yaml"

def test_basic_imports():
    """Test basic Python imports"""
    print("Testing basic Python imports...")
    
    try:
        import yaml
        print("✅ PyYAML import successful")
    except ImportError as e:
        print(f"❌ PyYAML import failed: {e}")
    
    try:
        import psutil
        print("✅ psutil import successful")
    except ImportError as e:
        print(f"❌ psutil import failed: {e}")
    
    try:
        import netifaces
        print("✅ netifaces import successful")
    except ImportError as e:
        print(f"❌ netifaces import failed: {e}")
    
    try:
        import cv2
        print("✅ OpenCV import successful")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
    
    try:
        import flask
        print("✅ Flask import successful")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")

def test_config_loading():
    """Test configuration file loading"""
    print(f"\nTesting config loading from: {CONFIG_PATH}")
    
    try:
        import yaml
        
        if not CONFIG_PATH.exists():
            print(f"❌ Config file not found: {CONFIG_PATH}")
            return False
            
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            
        print("✅ Config file loaded successfully")
        print(f"   Network interface: {config.get('network', {}).get('wifi_interface', 'Not set')}")
        print(f"   AP SSID: {config.get('network', {}).get('ap_config', {}).get('ssid', 'Not set')}")
        return True
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

# Test AP manager (import only)
print("\nTesting AP manager...")
try:
    from ap_manager import APManager
    
    # Test config loading
    ap = APManager(str(CONFIG_PATH))
    print("✅ AP manager import and config loading successful")
    
    # Test interface checking
    import netifaces
    interfaces = netifaces.interfaces()
    print(f"✅ Available interfaces: {interfaces}")
    
except Exception as e:
    print(f"❌ AP manager test failed: {e}")

# Test network monitor (import only)
print("\nTesting network monitor...")
try:
    from network_monitor import NetworkMonitor
    
    monitor = NetworkMonitor(str(CONFIG_PATH))
    print("✅ Network monitor import and config loading successful")
    
except Exception as e:
    print(f"❌ Network monitor test failed: {e}")

# Test camera streamer (import only)
print("\nTesting camera streamer...")
try:
    from camera_streamer import CameraStreamer
    
    streamer = CameraStreamer(str(CONFIG_PATH))
    print("✅ Camera streamer import and config loading successful")
    
except Exception as e:
    print(f"❌ Camera streamer test failed: {e}")

# Test web dashboard (import only)
print("\nTesting web dashboard...")
try:
    from web_dashboard import WebDashboard
    
    dashboard = WebDashboard(str(CONFIG_PATH))
    print("✅ Web dashboard import and config loading successful")
    
except Exception as e:
    print(f"❌ Web dashboard test failed: {e}")

def main():
    """Main test function"""
    print("=== Radxa Rock5B+ System Functionality Test ===")
    print(f"Script directory: {SCRIPT_DIR}")
    print(f"Config path: {CONFIG_PATH}")
    
    # Run basic tests
    test_basic_imports()
    config_ok = test_config_loading()
    
    if config_ok:
        print("\n=== All basic tests completed ===")
        print("Note: This is a basic functionality test.")
        print("Full system features require root privileges and proper hardware.")
    else:
        print("\n=== Tests completed with config issues ===")
        print("Please check your configuration file.")

if __name__ == "__main__":
    main()
