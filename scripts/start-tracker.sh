#!/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR/.." || exit 1

AWS_SECRET="$HOME/.aws_secret"

# Detect if running on Raspberry Pi
is_raspberry_pi() {
    # Check /proc/device-tree/model first (most reliable for Raspberry Pi)
    if [ -f /proc/device-tree/model ]; then
        if grep -qi "raspberry pi" /proc/device-tree/model 2>/dev/null; then
            return 0
        fi
    fi
    
    # Fallback: Check /proc/cpuinfo for Raspberry Pi hardware
    if [ -f /proc/cpuinfo ]; then
        if grep -qi "raspberry pi" /proc/cpuinfo 2>/dev/null; then
            return 0
        fi
    fi
    
    return 1
}

# Run appropriate command based on system type
if is_raspberry_pi; then
    echo "Detected Raspberry Pi - running directly with system Python"
    python src/app.py "$AWS_SECRET"
else
    echo "Detected non-Raspberry Pi system - using pipenv"
    pipenv sync
    pipenv run python src/app.py "$AWS_SECRET"
fi
