#!/bin/bash
# Simple dashboard start script

echo "🛡️  Starting Dashboard..."
echo ""

# Get to the right directory
cd "$(dirname "$0")" || exit 1
pwd

# Check Python
echo "Checking Python..."
python3 --version || exit 1

# Check dependencies
echo "Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip3 install --user Flask flask-socketio python-socketio eventlet 2>&1 | tail -3
fi

# Check if dependencies are now available
if ! python3 -c "import flask; import flask_socketio" 2>/dev/null; then
    echo "❌ Dependencies not available. Trying to install..."
    pip3 install --break-system-packages Flask flask-socketio python-socketio eventlet 2>&1 | tail -3
fi

# Verify
if python3 -c "import flask; import flask_socketio" 2>/dev/null; then
    echo "✅ Dependencies OK"
else
    echo "❌ Dependencies failed. Please install manually:"
    echo "   pip3 install Flask flask-socketio python-socketio eventlet"
    exit 1
fi

echo ""
echo "Starting dashboard server..."
echo "Access at: http://localhost:5001 or http://136.112.137.224:5001"
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
