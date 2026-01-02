#!/bin/bash

# Kill any existing Flask processes on port 5000
echo "Checking for existing processes on port 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null && echo "Freed port 5000" || echo "Port 5000 is available"

# Start the Flask web application
echo ""
echo "Starting Retraction Watch Dashboard Generator..."
echo "The app will automatically find an available port if 5000 is in use."
echo ""
python app.py

