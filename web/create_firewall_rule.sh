#!/bin/bash
# Script to create firewall rule for dashboard (run in Google Cloud Console or Cloud Shell)

echo "Creating firewall rule for dashboard (port 5001)..."
echo ""

# Try using gcloud if available
if command -v gcloud &> /dev/null; then
    echo "Using gcloud command..."
    gcloud compute firewall-rules create allow-dashboard-port \
        --allow tcp:5001 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow dashboard access on port 5001" \
        --direction INGRESS \
        --priority 1000
    
    if [ $? -eq 0 ]; then
        echo "✅ Firewall rule created successfully!"
        echo "Dashboard should now be accessible at: http://136.112.137.224:5001"
    else
        echo "❌ Failed to create firewall rule"
        echo "Please create it manually in the web console"
    fi
else
    echo "gcloud not found. Please create the rule manually:"
    echo ""
    echo "In Google Cloud Console:"
    echo "1. Click 'CREATE FIREWALL RULE'"
    echo "2. Name: allow-dashboard-port"
    echo "3. Direction: Ingress"
    echo "4. Action: Allow"
    echo "5. Targets: All instances in the network"
    echo "6. Source IP ranges: 0.0.0.0/0"
    echo "7. Protocols and ports: TCP, then enter: 5001"
    echo "8. Click CREATE"
fi

