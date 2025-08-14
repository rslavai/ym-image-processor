#!/bin/bash

# Setup Auto-deployment for YM Image Processor
# This script configures GitHub webhook auto-deployment on the server

set -e

echo "🚀 Setting up Auto-deployment for YM Image Processor"
echo "===================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
WEBHOOK_SECRET="ym-deploy-secret-2024"
PROJECT_DIR="/opt/ym-image-processor"
WEBHOOK_PORT=9000

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root or with sudo"
    exit 1
fi

# Step 1: Install Flask for webhook server
print_status "Installing Flask for webhook server..."
pip3 install flask

# Step 2: Clone or update repository
if [ ! -d "$PROJECT_DIR" ]; then
    print_status "Cloning repository..."
    cd /opt
    git clone https://github.com/rslavai/ym-image-processor.git
else
    print_status "Updating repository..."
    cd "$PROJECT_DIR"
    git pull origin main
fi

# Step 3: Copy webhook server
print_status "Setting up webhook server..."
cd "$PROJECT_DIR"

# Create webhook server if it doesn't exist
if [ ! -f "webhook_server.py" ]; then
    cat > webhook_server.py << 'EOF'
#!/usr/bin/env python3
"""
GitHub Webhook Server for Automatic Deployment
"""

from flask import Flask, request, jsonify
import hashlib
import hmac
import subprocess
import os
import json
import logging
from datetime import datetime
import threading

app = Flask(__name__)

WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'ym-deploy-secret-2024')
DEPLOY_SCRIPT = '/opt/deploy_ym.sh'
LOG_FILE = '/var/log/webhook_deploy.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verify_webhook_signature(payload_body, signature_header):
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)

def run_deployment():
    try:
        logger.info("Starting deployment...")
        
        if not os.path.exists(DEPLOY_SCRIPT):
            # Create deploy script if it doesn't exist
            with open(DEPLOY_SCRIPT, 'w') as f:
                f.write('''#!/bin/bash
cd /opt/ym-image-processor
git pull origin main
docker build -t ym-processor .
docker stop ym-processor || true
docker rm ym-processor || true
docker run -d --name ym-processor --restart always -p 8080:8080 --env-file .env ym-processor
''')
            os.chmod(DEPLOY_SCRIPT, 0o755)
        
        result = subprocess.run(
            ['/bin/bash', DEPLOY_SCRIPT],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            logger.info("Deployment completed successfully")
        else:
            logger.error(f"Deployment failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Deployment error: {e}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'webhook-server'})

@app.route('/webhook', methods=['POST'])
def github_webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    
    # For initial setup, allow without signature
    if signature and not verify_webhook_signature(request.data, signature):
        logger.warning("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 401
    
    try:
        payload = request.json
    except:
        return jsonify({'error': 'Invalid payload'}), 400
    
    event = request.headers.get('X-GitHub-Event', 'push')
    
    if event == 'ping':
        logger.info("Webhook ping successful")
        return jsonify({'message': 'Pong!'})
    
    if event != 'push':
        return jsonify({'message': f'Event {event} ignored'})
    
    # Check branch
    ref = payload.get('ref', '')
    if ref and 'main' not in ref:
        return jsonify({'message': 'Not main branch'})
    
    logger.info("Triggering deployment...")
    deployment_thread = threading.Thread(target=run_deployment)
    deployment_thread.daemon = True
    deployment_thread.start()
    
    return jsonify({'message': 'Deployment triggered'})

if __name__ == '__main__':
    logger.info("Starting webhook server on port 9000...")
    app.run(host='0.0.0.0', port=9000)
EOF
fi

chmod +x webhook_server.py

# Step 4: Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/webhook.service << EOF
[Unit]
Description=GitHub Webhook Server for YM Image Processor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment="WEBHOOK_SECRET=$WEBHOOK_SECRET"
ExecStart=/usr/bin/python3 $PROJECT_DIR/webhook_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/webhook_server.log
StandardError=append:/var/log/webhook_server.error.log

[Install]
WantedBy=multi-user.target
EOF

# Step 5: Create deploy script if it doesn't exist
if [ ! -f "/opt/deploy_ym.sh" ]; then
    print_status "Creating deploy script..."
    cat > /opt/deploy_ym.sh << 'EOF'
#!/bin/bash
set -e
cd /opt/ym-image-processor
git pull origin main

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << 'ENVEOF'
FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5
LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors
OPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw
PORT=8080
ENVEOF
fi

docker build -t ym-processor .
docker stop ym-processor || true
docker rm ym-processor || true
docker run -d \
    --name ym-processor \
    --restart always \
    -p 8080:8080 \
    --env-file .env \
    -v $(pwd)/database:/app/database \
    -v $(pwd)/processed:/app/processed \
    -v $(pwd)/uploads:/app/uploads \
    ym-processor

echo "Deployment completed at $(date)"
EOF
    chmod +x /opt/deploy_ym.sh
fi

# Step 6: Enable and start webhook service
print_status "Starting webhook service..."
systemctl daemon-reload
systemctl enable webhook.service
systemctl restart webhook.service

# Step 7: Configure firewall
print_status "Configuring firewall..."
ufw allow $WEBHOOK_PORT/tcp 2>/dev/null || print_warning "Firewall not configured"

# Step 8: Test webhook server
sleep 3
if curl -s http://localhost:$WEBHOOK_PORT/health | grep -q "healthy"; then
    print_status "Webhook server is running!"
else
    print_error "Webhook server failed to start. Check logs: journalctl -u webhook -n 50"
fi

# Step 9: Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")

echo ""
echo "===================================================="
print_status "Auto-deployment setup completed!"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Add webhook in GitHub repository settings:"
echo "   • Go to: https://github.com/rslavai/ym-image-processor/settings/hooks"
echo "   • Click 'Add webhook'"
echo "   • Payload URL: http://$SERVER_IP:$WEBHOOK_PORT/webhook"
echo "   • Content type: application/json"
echo "   • Secret: $WEBHOOK_SECRET"
echo "   • Select events: Just the push event"
echo "   • Active: ✓"
echo ""
echo "2. Test the webhook:"
echo "   • Make a small change to README.md"
echo "   • Commit and push to main branch"
echo "   • Check deployment: docker logs ym-processor"
echo ""
echo "📊 Useful commands:"
echo "   • Check webhook logs: journalctl -u webhook -f"
echo "   • Check deploy logs: tail -f /var/log/webhook_deploy.log"
echo "   • Restart webhook: systemctl restart webhook"
echo "   • Manual deploy: curl -X POST -H 'X-Deploy-Secret: $WEBHOOK_SECRET' http://localhost:$WEBHOOK_PORT/deploy"
echo ""
echo "🔒 Security note:"
echo "   The webhook secret is: $WEBHOOK_SECRET"
echo "   Keep this secret safe and use it in GitHub webhook settings"
echo ""
echo "✨ Your server will now auto-deploy on every push to main branch!"