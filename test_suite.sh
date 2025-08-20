#!/bin/bash

# Complete System Test Script
# Tests all components and generates a deployment report

echo "🧪 Radxa Rock5B+ System Test Suite"
echo "=================================="
echo ""

# Test variables
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Function to record test results
test_result() {
    case $1 in
        "PASS")
            echo "✅ $2"
            ((PASS_COUNT++))
            ;;
        "FAIL")
            echo "❌ $2"
            ((FAIL_COUNT++))
            ;;
        "WARN")
            echo "⚠️  $2"
            ((WARN_COUNT++))
            ;;
    esac
}

echo "1. Testing Script Syntax"
echo "------------------------"

# Test shell script syntax
if bash -n scripts/install.sh 2>/dev/null; then
    test_result "PASS" "install.sh syntax check"
else
    test_result "FAIL" "install.sh syntax check"
fi

if bash -n scripts/deploy.sh 2>/dev/null; then
    test_result "PASS" "deploy.sh syntax check"
else
    test_result "FAIL" "deploy.sh syntax check"
fi

echo ""
echo "2. Testing Python Script Compilation"
echo "------------------------------------"

# Test Python script compilation
python3 -m py_compile src/ap_manager.py 2>/dev/null && test_result "PASS" "ap_manager.py compilation" || test_result "FAIL" "ap_manager.py compilation"
python3 -m py_compile src/network_monitor.py 2>/dev/null && test_result "PASS" "network_monitor.py compilation" || test_result "FAIL" "network_monitor.py compilation"
python3 -m py_compile src/bandwidth_calculator.py 2>/dev/null && test_result "PASS" "bandwidth_calculator.py compilation" || test_result "FAIL" "bandwidth_calculator.py compilation"

echo ""
echo "3. Testing Configuration Files"
echo "------------------------------"

# Test YAML syntax
if python3 -c "import yaml; yaml.safe_load(open('config/settings.yaml'))" 2>/dev/null; then
    test_result "PASS" "settings.yaml syntax"
else
    test_result "FAIL" "settings.yaml syntax"
fi

if python3 -c "import yaml; yaml.safe_load(open('config/bandwidth_examples.yaml'))" 2>/dev/null; then
    test_result "PASS" "bandwidth_examples.yaml syntax"
else
    test_result "FAIL" "bandwidth_examples.yaml syntax"
fi

echo ""
echo "4. Testing File Structure"
echo "-------------------------"

# Check required directories
[ -d "src" ] && test_result "PASS" "src/ directory exists" || test_result "FAIL" "src/ directory missing"
[ -d "config" ] && test_result "PASS" "config/ directory exists" || test_result "FAIL" "config/ directory missing"
[ -d "scripts" ] && test_result "PASS" "scripts/ directory exists" || test_result "FAIL" "scripts/ directory missing"
[ -d "web/templates" ] && test_result "PASS" "web/templates/ directory exists" || test_result "FAIL" "web/templates/ directory missing"
[ -d "systemd" ] && test_result "PASS" "systemd/ directory exists" || test_result "FAIL" "systemd/ directory missing"
[ -d "docs" ] && test_result "PASS" "docs/ directory exists" || test_result "FAIL" "docs/ directory missing"

echo ""
echo "5. Testing Required Files"
echo "-------------------------"

# Check critical files
required_files=(
    "requirements.txt"
    "config/settings.yaml"
    "src/ap_manager.py"
    "src/network_monitor.py"
    "src/camera_streamer.py"
    "src/web_dashboard.py"
    "src/bandwidth_calculator.py"
    "scripts/install.sh"
    "scripts/deploy.sh"
    "web/templates/dashboard.html"
    "systemd/radxa-manager.service"
    "systemd/radxa-network-monitor.service"
    "docs/USER_GUIDE.md"
    "QUICKSTART.md"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        test_result "PASS" "$file exists"
    else
        test_result "FAIL" "$file missing"
    fi
done

echo ""
echo "6. Testing File Permissions"
echo "---------------------------"

# Check executable permissions
[ -x "scripts/install.sh" ] && test_result "PASS" "install.sh is executable" || test_result "WARN" "install.sh not executable (will be fixed during transfer)"
[ -x "scripts/deploy.sh" ] && test_result "PASS" "deploy.sh is executable" || test_result "WARN" "deploy.sh not executable"

echo ""
echo "7. Testing Help Functionality"
echo "-----------------------------"

# Test help outputs
if scripts/deploy.sh --help >/dev/null 2>&1; then
    test_result "PASS" "deploy.sh --help works"
else
    test_result "FAIL" "deploy.sh --help failed"
fi

echo ""
echo "8. Testing HTML Template"
echo "------------------------"

# Basic HTML structure check
if grep -q "<!DOCTYPE html>" web/templates/dashboard.html; then
    test_result "PASS" "HTML template has DOCTYPE"
else
    test_result "FAIL" "HTML template missing DOCTYPE"
fi

if grep -q "</html>" web/templates/dashboard.html; then
    test_result "PASS" "HTML template properly closed"
else
    test_result "FAIL" "HTML template not properly closed"
fi

echo ""
echo "9. Generating Deployment Package"
echo "--------------------------------"

# Create deployment package info
TOTAL_FILES=$(find . -type f | wc -l)
TOTAL_SIZE=$(du -sh . | cut -f1)

test_result "PASS" "Total files: $TOTAL_FILES"
test_result "PASS" "Package size: $TOTAL_SIZE"

echo ""
echo "10. System Requirements Check"
echo "----------------------------"

# Check if current system has required tools
command -v python3 >/dev/null && test_result "PASS" "Python 3 available" || test_result "WARN" "Python 3 not found"
command -v ssh >/dev/null && test_result "PASS" "SSH client available" || test_result "WARN" "SSH client not found"
command -v scp >/dev/null && test_result "PASS" "SCP available" || test_result "WARN" "SCP not found"
command -v rsync >/dev/null && test_result "PASS" "rsync available" || test_result "WARN" "rsync not found (will use scp)"

echo ""
echo "=================================================="
echo "TEST RESULTS SUMMARY"
echo "=================================================="
echo "✅ Passed: $PASS_COUNT"
echo "❌ Failed: $FAIL_COUNT"  
echo "⚠️  Warnings: $WARN_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 ALL CRITICAL TESTS PASSED!"
    echo "The system is ready for deployment to Radxa Rock5B+"
    echo ""
    echo "Quick deployment command:"
    echo "./scripts/deploy.sh <radxa-ip> --install --start"
    echo ""
    echo "Example with SSH key:"
    echo "./scripts/deploy.sh 192.168.1.100 -k ~/.ssh/id_rsa --install --start"
    exit 0
else
    echo "💥 CRITICAL FAILURES DETECTED!"
    echo "Please fix the failed tests before deployment"
    exit 1
fi
