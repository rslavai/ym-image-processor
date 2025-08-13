#!/bin/bash
# Commands to run on the server manually
# Copy and paste these commands after connecting to the server via SSH

echo "======================================"
echo "🚀 YM Image Processor Server Setup"
echo "======================================"
echo ""
echo "Run these commands on your server:"
echo ""

cat << 'EOF'
# 1. Install required packages
apt-get update
apt-get install -y git docker.io python3 python3-pip curl ufw

# 2. Start and enable Docker
systemctl start docker
systemctl enable docker

# 3. Setup project directory
mkdir -p /opt/ym-image-processor
cd /opt

# 4. Clone repository (or update if exists)
if [ -d "ym-image-processor/.git" ]; then
    echo "Repository exists, updating..."
    cd ym-image-processor
    git pull origin main || {
        echo "Git pull failed, resetting..."
        git fetch --all
        git reset --hard origin/main
    }
else
    echo "Cloning repository..."
    git clone https://github.com/rslavai/ym-image-processor.git
    cd ym-image-processor
fi

# 5. Create .env file
cat > .env << 'ENVEOF'
FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5
LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors
OPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw
PORT=8080
WEBHOOK_SECRET=ym-deploy-secret-2024
ENVEOF

# 6. Build and start application
docker stop ym-processor 2>/dev/null || true
docker rm ym-processor 2>/dev/null || true
docker build -t ym-processor .
docker run -d \
    --name ym-processor \
    --restart always \
    -p 8080:8080 \
    --env-file .env \
    ym-processor

# 7. Setup webhook server
pip3 install flask requests

# 8. Create webhook systemd service
cat > /etc/systemd/system/ym-webhook.service << 'SERVICEEOF'
[Unit]
Description=YM Image Processor Webhook Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ym-image-processor
Environment="WEBHOOK_SECRET=ym-deploy-secret-2024"
ExecStart=/usr/bin/python3 /opt/ym-image-processor/webhook_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICEEOF

# 9. Start webhook service
systemctl daemon-reload
systemctl enable ym-webhook
systemctl start ym-webhook

# 10. Configure firewall
ufw --force enable
ufw allow 22/tcp
ufw allow 8080/tcp
ufw allow 9000/tcp

# 11. Check status
echo "🔍 Checking application status..."
docker ps | grep ym-processor
echo ""
echo "🔍 Checking webhook status..."
systemctl status ym-webhook --no-pager -l
echo ""
echo "✅ Setup completed!"
echo "Application: http://103.136.69.249:8080"
echo "Webhook: http://103.136.69.249:9000/webhook"
EOF