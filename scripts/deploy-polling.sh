#!/bin/bash
# KI Ecosystem Auto-Pull Script for Polling CI/CD
# Run via systemd timer every 5 minutes on target hosts
# 
# Logs to: ~/dev_data/ki-ecosystem/log/polling.log

set -e

# Configuration
ECOSYSTEM_ROOT="/home/flow/dev_flow/ki-ecosystem"
LOG_DIR="$HOME/dev_data/ki-ecosystem/log"
LOG_FILE="$LOG_DIR/polling.log"

# Ensure log directory exists and is writable
mkdir -p "$LOG_DIR" 2>/dev/null || true
chmod 700 "$LOG_DIR" 2>/dev/null || true

# Log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE" 2>&1 || true
}

{
    log "=== Starting automated pull ==="
    log "User: $(whoami)"
    log "HOME: $HOME"
    log "PATH: $PATH"
    
    # Check if ecosystem root exists
    if [ ! -d "$ECOSYSTEM_ROOT" ]; then
        log "ERROR: $ECOSYSTEM_ROOT does not exist"
        exit 1
    fi
    
    # Change to ecosystem root
    cd "$ECOSYSTEM_ROOT" || {
        log "ERROR: Cannot cd to $ECOSYSTEM_ROOT"
        exit 1
    }
    log "Working directory: $(pwd)"
    
    # Try to find stackctl - use full path
    STACKCTL=$(which stackctl 2>/dev/null)
    if [ -z "$STACKCTL" ]; then
        # Common locations if which fails
        for path in /home/flow/.local/bin/stackctl /usr/local/bin/stackctl /usr/bin/stackctl; do
            if [ -x "$path" ]; then
                STACKCTL="$path"
                break
            fi
        done
    fi
    
    if [ -z "$STACKCTL" ]; then
        log "ERROR: stackctl not found in PATH"
        exit 1
    fi
    
    log "Using stackctl: $STACKCTL"
    
    # Run stackctl pull
    if $STACKCTL pull 2>&1; then
        log "✓ stackctl pull succeeded"
    else
        EXIT_CODE=$?
        log "✗ stackctl pull failed (exit code: $EXIT_CODE)"
        exit $EXIT_CODE
    fi
    
    # Show status
    $STACKCTL repo-status 2>&1 | head -20 >> "$LOG_FILE"
    
    log "=== Completed automated pull ==="
} >> "$LOG_FILE" 2>&1

exit 0

