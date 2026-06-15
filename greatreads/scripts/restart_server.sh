#!/bin/bash
# Restart the GreatReads server via systemd

echo "🔄 Restarting GreatReads server via systemd..."

# Restart the systemd service
sudo systemctl restart greatreads

# Wait a moment for the service to start
sleep 2

# Check status
echo ""
echo "✅ Server status:"
sudo systemctl status greatreads --no-pager -l | head -15

