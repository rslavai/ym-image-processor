#!/bin/bash
# Simple deployment script using password authentication

SERVER_IP="103.136.69.249"
SERVER_USER="root"
PUBLIC_KEY=$(cat ~/.ssh/ym_server_key.pub)

echo "🚀 Deploying YM Image Processor to $SERVER_IP"
echo "This script will prompt for password multiple times..."

# Step 1: Setup SSH key
echo "📋 Step 1: Installing SSH key for passwordless access..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << ENDSSH
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.tmp
mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys
echo "✅ SSH key installed"
ENDSSH

# Test passwordless connection
echo "✅ Testing SSH key authentication..."
if ssh -i ~/.ssh/ym_server_key -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "echo 'SSH key works!'"; then
    echo "✅ SSH key authentication successful!"
    USE_KEY=true
else
    echo "⚠️ SSH key authentication failed, will use password"
    USE_KEY=false
fi

# Determine SSH command
if [ "$USE_KEY" = true ]; then
    SSH_CMD="ssh -i ~/.ssh/ym_server_key $SERVER_USER@$SERVER_IP"
else
    SSH_CMD="ssh $SERVER_USER@$SERVER_IP"
fi

# Step 2: Setup project
echo "📋 Step 2: Setting up project directory..."
$SSH_CMD << 'ENDSSH'
set -e

# Install required packages
apt-get update
apt-get install -y git docker.io python3 python3-pip curl

# Start Docker
systemctl start docker
systemctl enable docker

# Create project directory
mkdir -p /opt/ym-image-processor
cd /opt

# Clone or update repository
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

# Create .env file
echo "Creating .env file..."
cat > .env << 'EOF'
FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5
LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors
OPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw
PORT=8080
WEBHOOK_SECRET=ym-deploy-secret-2024
EOF

echo "✅ Project setup completed"
ENDSSH

# Step 3: Build and deploy application
echo "📋 Step 3: Building and starting application..."
$SSH_CMD << 'ENDSSH'
cd /opt/ym-image-processor

# Stop existing container
echo "Stopping existing container..."
docker stop ym-processor 2>/dev/null || true
docker rm ym-processor 2>/dev/null || true

# Build new image
echo "Building Docker image..."
docker build -t ym-processor .

# Start container
echo "Starting new container..."
docker run -d \
    --name ym-processor \
    --restart always \
    -p 8080:8080 \
    --env-file .env \
    ym-processor

# Wait for container to start
sleep 10

# Check container status
if docker ps | grep -q ym-processor; then
    echo "✅ Application container started successfully"
    docker logs --tail 5 ym-processor
else
    echo "❌ Application container failed to start"
    docker logs ym-processor
    exit 1
fi
ENDSSH

# Step 4: Setup webhook server
echo "📋 Step 4: Setting up webhook for auto-deploy..."
$SSH_CMD << 'ENDSSH'
cd /opt/ym-image-processor

# Install webhook dependencies
pip3 install flask requests

# Create webhook systemd service
cat > /etc/systemd/system/ym-webhook.service << 'EOF'
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
EOF

# Reload systemd and start webhook
systemctl daemon-reload
systemctl enable ym-webhook
systemctl restart ym-webhook

# Wait for webhook to start
sleep 5

# Check webhook status
if systemctl is-active --quiet ym-webhook; then
    echo "✅ Webhook server started successfully"
    echo "Webhook listening on port 9000"
else
    echo "❌ Webhook server failed to start"
    journalctl -u ym-webhook --no-pager -n 10
fi

# Configure firewall
ufw --force enable
ufw allow 22/tcp
ufw allow 8080/tcp
ufw allow 9000/tcp

echo "🎉 Deployment completed successfully!"
echo ""
echo "🌐 Services:"
echo "  Application: http://103.136.69.249:8080"
echo "  Webhook: http://103.136.69.249:9000/webhook"
echo ""
echo "🔐 Webhook Secret: ym-deploy-secret-2024"
ENDSSH

echo ""
echo "✅ All setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Test application: http://103.136.69.249:8080"
echo "2. Setup GitHub webhook with:"
echo "   URL: http://103.136.69.249:9000/webhook"
echo "   Secret: ym-deploy-secret-2024"
echo "   Content-Type: application/json"
echo "3. Push to main branch will trigger auto-deploy"