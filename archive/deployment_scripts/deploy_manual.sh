#!/bin/bash

# Manual deployment script for YM Image Processor
# Usage: ./deploy_manual.sh

SERVER_IP="103.136.69.249"
SERVER_USER="root"

echo "🚀 Starting manual deployment to $SERVER_IP"

# Function to run SSH command
run_ssh() {
    ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "$1"
}

# Test connection
echo "Testing SSH connection..."
if ! run_ssh "echo 'Connection successful'"; then
    echo "❌ Cannot connect to server. Please check:"
    echo "1. Server is running"
    echo "2. SSH service is active"
    echo "3. You have the correct SSH key"
    exit 1
fi

echo "✅ Connection successful"

# Deploy
echo "Starting deployment..."
run_ssh "bash -s" << 'ENDSSH'
set -e

echo "📦 Checking repository..."
if [ ! -d "/opt/ym-image-processor" ]; then
    echo "Cloning repository..."
    cd /opt
    git clone https://github.com/rslavai/ym-image-processor.git
fi

cd /opt/ym-image-processor

echo "📥 Pulling latest changes..."
git pull origin main || {
    echo "Git pull failed, resetting..."
    git fetch --all
    git reset --hard origin/main
}

echo "🔧 Creating .env file..."
cat > .env << 'EOF'
# Официальный ключ для fal_client
FAL_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5
# Резервный ключ для совместимости
FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5
LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors
OPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw
PORT=8080
EOF

echo "🔍 Checking environment..."
python3 check_production_env.py || {
    echo "❌ Environment check failed"
    echo "Continuing with deployment anyway..."
}

echo "🐳 Building Docker image..."
docker build -t ym-processor .

echo "🔄 Restarting container..."
docker stop ym-processor 2>/dev/null || true
docker rm ym-processor 2>/dev/null || true

docker run -d \
  --name ym-processor \
  --restart always \
  -p 8080:8080 \
  --env-file .env \
  ym-processor

echo "⏳ Waiting for container to start..."
sleep 5

if docker ps | grep -q ym-processor; then
    echo "✅ Container is running!"
    docker logs --tail 20 ym-processor
else
    echo "❌ Container failed to start"
    docker logs ym-processor
    exit 1
fi
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment completed successfully!"
    echo "🌐 Your service is available at: http://$SERVER_IP"
    echo ""
    
    # Test the service
    echo "Testing service health..."
    curl -s --max-time 5 http://$SERVER_IP/health | python3 -m json.tool || echo "Service may still be starting up..."
else
    echo "❌ Deployment failed"
    exit 1
fi