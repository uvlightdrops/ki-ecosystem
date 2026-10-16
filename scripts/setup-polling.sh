#!/bin/bash
# Setup ki-ecosystem CI/CD polling on target host
# 
# Usage: sudo bash setup-polling.sh
# 
# This script:
# 1. Clones ki-ecosystem repo (if not already cloned)
# 2. Copies systemd service/timer files to /etc/systemd/system/
# 3. Runs systemctl daemon-reload and enables the timer

set -e

# Configuration
DEV_FLOW_DIR="/home/flow/dev_flow"
DEV_DATA_DIR="/home/flow/dev_data"
ECOSYSTEM_REPO="https://github.com/uvlightdrops/ki-ecosystem.git"
ECOSYSTEM_DIR="$DEV_FLOW_DIR/ki-ecosystem"
LOG_DIR="$DEV_DATA_DIR/ki-ecosystem/log"

echo "=== KI Ecosystem Polling Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo"
    exit 1
fi

# Create dev_flow directory if it doesn't exist
if [ ! -d "$DEV_FLOW_DIR" ]; then
    echo "Creating $DEV_FLOW_DIR"
    mkdir -p "$DEV_FLOW_DIR"
    chown flow:flow "$DEV_FLOW_DIR"
fi

# Create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating $LOG_DIR"
    mkdir -p "$LOG_DIR"
    chown flow:flow "$LOG_DIR"
    chmod 700 "$LOG_DIR"
fi

# Clone ki-ecosystem if it doesn't exist
if [ ! -d "$ECOSYSTEM_DIR" ]; then
    echo "Cloning ki-ecosystem from $ECOSYSTEM_REPO"
    cd "$DEV_FLOW_DIR"
    sudo -u flow git clone "$ECOSYSTEM_REPO" ki-ecosystem
else
    echo "ki-ecosystem already exists at $ECOSYSTEM_DIR"
    echo "Pulling latest changes..."
    cd "$ECOSYSTEM_DIR"
    sudo -u flow git pull
fi

# Verify systemd files exist
if [ ! -f "$ECOSYSTEM_DIR/scripts/ki-ecosystem-polling.service" ]; then
    echo "ERROR: service file not found at $ECOSYSTEM_DIR/scripts/ki-ecosystem-polling.service"
    exit 1
fi

if [ ! -f "$ECOSYSTEM_DIR/scripts/ki-ecosystem-polling.timer" ]; then
    echo "ERROR: timer file not found at $ECOSYSTEM_DIR/scripts/ki-ecosystem-polling.timer"
    exit 1
fi

# Copy systemd files to /etc/systemd/system/
echo "Copying systemd service and timer files..."
cp "$ECOSYSTEM_DIR/scripts/ki-ecosystem-polling.service" /etc/systemd/system/
cp "$ECOSYSTEM_DIR/scripts/ki-ecosystem-polling.timer" /etc/systemd/system/

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start the timer
echo "Enabling ki-ecosystem-polling.timer..."
systemctl enable ki-ecosystem-polling.timer

echo "Starting ki-ecosystem-polling.timer..."
systemctl start ki-ecosystem-polling.timer

# Show status
echo ""
echo "=== Setup Complete ==="
systemctl status ki-ecosystem-polling.timer
echo ""
echo "Polling logs:"
echo "  tail -f ~/dev_data/ki-ecosystem/log/polling.log"
echo ""
echo "Systemd logs:"
echo "  journalctl -u ki-ecosystem-polling.service -f"
echo ""
echo "Timer schedule:"
echo "  systemctl list-timers ki-ecosystem-polling"
