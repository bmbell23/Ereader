#!/bin/bash
# Keep the static web server alive with auto-restart on crash
# Usage: ./keep-alive.sh &

cd "$(dirname "$0")"
LOG_FILE="/tmp/ereader-static.log"
PID_FILE="/tmp/ereader-static.pid"

# Kill any existing instances
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Stopping old server (PID $OLD_PID)"
        kill "$OLD_PID" 2>/dev/null
        sleep 1
    fi
fi

echo "Starting Ereader static server watchdog..."
echo "Log: $LOG_FILE"
echo "PID: $$" > "$PID_FILE"

while true; do
    # Check if server is running on port 8090
    if ! ss -ltn | grep -q ":8090 "; then
        echo "[$(date)] Server not found on port 8090, starting..."
        
        # Clean up any stale processes
        pkill -f "python3 serve.py" 2>/dev/null
        sleep 1
        
        # Start the server
        python3 serve.py >> "$LOG_FILE" 2>&1 &
        SERVER_PID=$!
        
        echo "[$(date)] Started server with PID $SERVER_PID"
        sleep 2
        
        # Verify it started
        if ss -ltn | grep -q ":8090 "; then
            echo "[$(date)] Server is UP on port 8090"
        else
            echo "[$(date)] ERROR: Server failed to start!"
            tail -20 "$LOG_FILE"
        fi
    fi
    
    # Check every 5 seconds
    sleep 5
done
