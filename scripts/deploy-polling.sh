#!/bin/bash
# KI Ecosystem Auto-Pull Script for Polling CI/CD
# Run via systemd timer every 5 minutes on target hosts
# 
# Setup on target host:
#   sudo cp scripts/deploy-polling.sh /opt/ki-ecosystem-polling.sh
#   sudo chmod +x /opt/ki-ecosystem-polling.sh
#   sudo cp scripts/ki-ecosystem-polling.{service,timer} /etc/systemd/system/
#   sudo systemctl daemon-reload
#   sudo systemctl enable --now ki-ecosystem-polling.timer
#   sudo systemctl status ki-ecosystem-polling.timer

set -e

# Configuration
ECOSYSTEM_ROOT="$HOME/dev_flow/ki-ecosystem"
LOG_FILE="$HOME/.ki-ecosystem/polling.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

log "=== Starting automated pull ==="

# Change to ecosystem root
cd "$ECOSYSTEM_ROOT" || {
    log "ERROR: Cannot cd to $ECOSYSTEM_ROOT"
    exit 1
}

# Run stackctl pull
if stackctl pull >> "$LOG_FILE" 2>&1; then
    log "✓ stackctl pull succeeded"
else
    log "✗ stackctl pull failed (exit code: $?)"
    exit 1
fi

# Show status
stackctl repo-status >> "$LOG_FILE" 2>&1

log "=== Completed automated pull ==="
