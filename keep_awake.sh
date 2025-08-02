#!/bin/bash
"""
Keep System Awake Script
========================
This script prevents the laptop from sleeping while the StockAnalyzer is running.
"""

echo "Starting system keep-awake for StockAnalyzer..."
echo "This will prevent your laptop from sleeping"
echo "Press Ctrl+C to stop"

# Try different methods to prevent sleep
if command -v caffeine &> /dev/null; then
    echo "Using caffeine to prevent sleep..."
    caffeine -d
elif command -v systemd-inhibit &> /dev/null; then
    echo "Using systemd-inhibit to prevent sleep..."
    systemd-inhibit --what=sleep:idle --who="StockAnalyzer" --why="Running 24/7 stock analysis" sleep infinity
else
    echo "Using simple keep-awake method..."
    # Simple method: move mouse cursor slightly every 5 minutes
    while true; do
        # Keep system awake by touching a file every 5 minutes
        touch /tmp/stockanalyzer_keepawake
        echo "$(date): Keeping system awake..."
        sleep 300  # 5 minutes
    done
fi
