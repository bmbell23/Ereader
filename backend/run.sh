#!/bin/bash

# Example usage:
# export CALIBRE_URL="http://localhost:8083"
# export CALIBRE_LIBRARY="library"
# ./run.sh

# Use defaults if not set
if [ -z "$CALIBRE_URL" ]; then
    export CALIBRE_URL="http://localhost:8083"
    echo "Using default CALIBRE_URL: $CALIBRE_URL"
fi

if [ -z "$CALIBRE_LIBRARY" ]; then
    export CALIBRE_LIBRARY="library"
    echo "Using default CALIBRE_LIBRARY: $CALIBRE_LIBRARY"
fi

echo "Starting Ereader Backend Server..."
echo "Calibre URL: $CALIBRE_URL"
echo "Calibre Library: $CALIBRE_LIBRARY"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

python server.py
