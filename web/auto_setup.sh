#!/bin/bash
# Automated setup and start script for web dashboard

set -e

echo "🛡️  Linux Security Agent - Dashboard Auto Setup"
echo "================================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Step 1: Pull latest code
echo "Step 1: Updating code..."
git pull origin main || echo "⚠️  Git pull failed (may not be a git repo)"
echo "✅ Code updated"
echo ""

# Step 2: Check dependencies
echo "Step 2: Checking dependencies..."
cd "$SCRIPT_DIR"

if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask dependencies..."
    pip3 install --user Flask flask-socketio python-socketio eventlet requests 2>&1 | grep -E "(Successfully|Requirement|ERROR)" || true
fi

if python3 -c "import flask; import flask_socketio" 2>/dev/null; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Step 3: Create logs directory
echo "Step 3: Setting up directories..."
mkdir -p "$PROJECT_ROOT/logs"
chmod 755 "$PROJECT_ROOT/logs"
echo "✅ Directories ready"
echo ""

# Step 4: Kill any existing dashboard
echo "Step 4: Cleaning up..."
pkill -f "app.py" 2>/dev/null || true
sleep 2
echo "✅ Cleanup done"
echo ""

# Step 5: Get network info
echo "Step 5: Network information..."
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "136.112.137.224")
echo "   Local IP: $LOCAL_IP"
echo "   Public IP: $PUBLIC_IP"
echo ""

# Step 6: Start dashboard
echo "Step 6: Starting dashboard..."
echo ""
echo "=========================================="
echo "🛡️  Dashboard Starting"
echo "=========================================="
echo ""
echo "Access the dashboard at:"
echo "  1. http://localhost:5001 (from VM)"
echo "  2. http://$PUBLIC_IP:5001 (from your browser)"
echo ""
echo "If option 2 doesn't work, add firewall rule:"
echo "  gcloud compute firewall-rules create allow-dashboard \\"
echo "    --allow tcp:5001 --source-ranges 0.0.0.0/0"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo "=========================================="
echo ""

cd "$SCRIPT_DIR"
python3 app.py

