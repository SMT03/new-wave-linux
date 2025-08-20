#!/bin/bash

# SSH Transfer Script for Radxa Rock5B+
# Transfer and install the management system to your Radxa device

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REMOTE_USER="radxa"
REMOTE_DIR="/home/$REMOTE_USER/radxa-system"

# Function to show usage
show_usage() {
    echo "Usage: $0 <radxa-ip-address> [options]"
    echo ""
    echo "Options:"
    echo "  -u, --user <username>     Remote username (default: radxa)"
    echo "  -p, --port <port>         SSH port (default: 22)"
    echo "  -k, --key <keyfile>       SSH private key file"
    echo "  -i, --install             Install after transfer"
    echo "  -s, --start               Start services after installation"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 192.168.1.100"
    echo "  $0 192.168.1.100 --install"
    echo "  $0 192.168.1.100 -u ubuntu -k ~/.ssh/radxa_key --install --start"
}

# Parse arguments
RADXA_IP=""
SSH_PORT="22"
SSH_KEY=""
INSTALL_FLAG=false
START_FLAG=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--user)
            REMOTE_USER="$2"
            shift 2
            ;;
        -p|--port)
            SSH_PORT="$2"
            shift 2
            ;;
        -k|--key)
            SSH_KEY="$2"
            shift 2
            ;;
        -i|--install)
            INSTALL_FLAG=true
            shift
            ;;
        -s|--start)
            START_FLAG=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [[ -z "$RADXA_IP" ]]; then
                RADXA_IP="$1"
            else
                print_error "Multiple IP addresses specified"
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$RADXA_IP" ]]; then
    print_error "Radxa IP address is required"
    show_usage
    exit 1
fi

# Validate IP address format
if ! [[ $RADXA_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
    print_error "Invalid IP address format: $RADXA_IP"
    exit 1
fi

# Build SSH command
SSH_CMD="ssh -p $SSH_PORT"
SCP_CMD="scp -P $SSH_PORT"

if [[ -n "$SSH_KEY" ]]; then
    if [[ ! -f "$SSH_KEY" ]]; then
        print_error "SSH key file not found: $SSH_KEY"
        exit 1
    fi
    SSH_CMD="$SSH_CMD -i $SSH_KEY"
    SCP_CMD="$SCP_CMD -i $SSH_KEY"
fi

REMOTE_HOST="$REMOTE_USER@$RADXA_IP"

print_status "🚀 Radxa Rock5B+ System Transfer Script"
echo "============================================"
echo "Target: $REMOTE_HOST"
echo "Remote directory: $REMOTE_DIR"
echo "SSH port: $SSH_PORT"
if [[ -n "$SSH_KEY" ]]; then
    echo "SSH key: $SSH_KEY"
fi
echo "Install after transfer: $INSTALL_FLAG"
echo "Start services: $START_FLAG"
echo ""

# Test SSH connection
print_status "Testing SSH connection..."
if ! $SSH_CMD -o ConnectTimeout=10 -o BatchMode=yes $REMOTE_HOST "echo 'SSH connection successful'" 2>/dev/null; then
    print_error "Failed to connect to $REMOTE_HOST"
    echo "Please check:"
    echo "  - IP address is correct"
    echo "  - SSH service is running on the Radxa"
    echo "  - SSH key is correct (if using key authentication)"
    echo "  - Network connectivity"
    exit 1
fi

print_success "SSH connection established"

# Create remote directory
print_status "Creating remote directory..."
$SSH_CMD $REMOTE_HOST "mkdir -p $REMOTE_DIR" || {
    print_error "Failed to create remote directory"
    exit 1
}

# Create temporary exclusion file for rsync
TEMP_EXCLUDE_FILE=$(mktemp)
cat > "$TEMP_EXCLUDE_FILE" << EOF
.git/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
.env
.coverage
.pytest_cache/
.idea/
.vscode/
*.log
*.tmp
.DS_Store
Thumbs.db
EOF

# Transfer files using rsync over SSH
print_status "Transferring files to Radxa..."
if command -v rsync &> /dev/null; then
    # Use rsync for efficient transfer
    rsync -avz --progress --delete \
        --exclude-from="$TEMP_EXCLUDE_FILE" \
        -e "$SSH_CMD" \
        "$PROJECT_DIR/" \
        "$REMOTE_HOST:$REMOTE_DIR/" || {
        print_error "File transfer failed"
        rm -f "$TEMP_EXCLUDE_FILE"
        exit 1
    }
else
    # Fallback to scp
    print_warning "rsync not available, using scp (slower)"
    $SCP_CMD -r "$PROJECT_DIR"/* "$REMOTE_HOST:$REMOTE_DIR/" || {
        print_error "File transfer failed"
        rm -f "$TEMP_EXCLUDE_FILE"
        exit 1
    }
fi

# Clean up temporary file
rm -f "$TEMP_EXCLUDE_FILE"

print_success "Files transferred successfully"

# Set executable permissions
print_status "Setting file permissions..."
$SSH_CMD $REMOTE_HOST "chmod +x $REMOTE_DIR/scripts/*.sh" || {
    print_warning "Failed to set some file permissions"
}

$SSH_CMD $REMOTE_HOST "chmod +x $REMOTE_DIR/src/*.py" || {
    print_warning "Failed to set some file permissions"
}

# Install if requested
if [[ "$INSTALL_FLAG" == true ]]; then
    print_status "Starting installation on Radxa..."
    
    # Check if we need to update package lists
    print_status "Checking if system needs updates..."
    $SSH_CMD $REMOTE_HOST "sudo apt update -qq" || {
        print_warning "Failed to update package lists"
    }
    
    # Run installation script
    $SSH_CMD $REMOTE_HOST "cd $REMOTE_DIR && sudo -E bash scripts/install.sh" || {
        print_error "Installation failed"
        exit 1
    }
    
    print_success "Installation completed successfully"
    
    # Start services if requested
    if [[ "$START_FLAG" == true ]]; then
        print_status "Starting services..."
        $SSH_CMD $REMOTE_HOST "sudo systemctl start radxa-manager radxa-network-monitor nginx" || {
            print_warning "Some services failed to start"
        }
        
        # Check service status
        print_status "Checking service status..."
        $SSH_CMD $REMOTE_HOST "sudo systemctl is-active radxa-manager" && \
        print_success "radxa-manager service is running" || \
        print_warning "radxa-manager service is not running"
        
        print_success "Services started"
    fi
fi

# Show connection information
print_success "Transfer completed successfully! 🎉"
echo ""
echo "📋 Next Steps:"
echo "=============="

if [[ "$INSTALL_FLAG" == false ]]; then
    echo "1. SSH to your Radxa:"
    echo "   ssh $REMOTE_HOST"
    echo ""
    echo "2. Navigate to the project directory:"
    echo "   cd $REMOTE_DIR"
    echo ""
    echo "3. Run the installation script:"
    echo "   sudo bash scripts/install.sh"
fi

echo ""
echo "🌐 Access the Web Dashboard:"
echo "==========================="
echo "URL: http://$RADXA_IP:8080"
echo ""
echo "🎮 Command Line Tools (on Radxa):"
echo "================================="
echo "radxa-start          - Start all services"
echo "radxa-stop           - Stop all services"
echo "radxa-status         - Show service status"
echo "radxa-ap --help      - Access Point management"
echo "radxa-camera --help  - Camera control"
echo "radxa-network --help - Network monitoring"
echo ""

# Test web dashboard availability if services are running
if [[ "$INSTALL_FLAG" == true ]] && [[ "$START_FLAG" == true ]]; then
    print_status "Testing web dashboard availability..."
    sleep 5  # Give services time to start
    
    if curl -s --connect-timeout 10 "http://$RADXA_IP:8080" > /dev/null 2>&1; then
        print_success "Web dashboard is accessible at http://$RADXA_IP:8080"
    else
        print_warning "Web dashboard may still be starting up. Please wait a moment and try accessing http://$RADXA_IP:8080"
    fi
fi

echo ""
echo "📖 Useful SSH Commands:"
echo "======================"
echo "Connect to Radxa:        ssh $REMOTE_HOST"
echo "View system logs:        ssh $REMOTE_HOST 'sudo journalctl -u radxa-manager -f'"
echo "Check service status:    ssh $REMOTE_HOST 'sudo systemctl status radxa-manager'"
echo "Restart services:        ssh $REMOTE_HOST 'sudo systemctl restart radxa-manager'"
echo ""
echo "🔄 System Management:"
echo "Quick reset:             ssh $REMOTE_HOST 'sudo /opt/radxa/scripts/reset.sh'"
echo "Full uninstall:          ssh $REMOTE_HOST 'sudo /opt/radxa/scripts/uninstall.sh'"
echo ""

print_success "Happy streaming with your Radxa Rock5B+! 📹🚀"
