#!/bin/bash
# Simple deployment in stages

SERVER_IP="103.136.69.249"
SERVER_USER="root" 
SERVER_PASSWORD="wBlO#rH6yDy2z0oB0J"

echo "🚀 Simple deployment to $SERVER_IP"

# Stage 1: Basic setup and Docker install
echo "📋 Stage 1: Installing Docker and basic packages..."
expect << 'EOF'
set timeout 60
spawn ssh -o StrictHostKeyChecking=no root@103.136.69.249
expect "password:" { send "wBlO#rH6yDy2z0oB0J\r" }
expect "# " {
    send "apt-get update\r"
    expect "# "
    send "apt-get install -y docker.io git python3 python3-pip curl\r"
    expect "# "
    send "systemctl start docker\r"
    expect "# "
    send "systemctl enable docker\r"
    expect "# "
    send "exit\r"
}
expect eof
EOF

echo "✅ Stage 1 completed"

# Stage 2: Clone repository and setup
echo "📋 Stage 2: Setting up repository..."
expect << 'EOF'
set timeout 60
spawn ssh -o StrictHostKeyChecking=no root@103.136.69.249
expect "password:" { send "wBlO#rH6yDy2z0oB0J\r" }
expect "# " {
    send "cd /opt\r"
    expect "# "
    send "rm -rf ym-image-processor\r"
    expect "# "
    send "git clone https://github.com/rslavai/ym-image-processor.git\r"
    expect "# "
    send "cd ym-image-processor\r"
    expect "# "
    send "ls -la\r"
    expect "# "
    send "exit\r"
}
expect eof
EOF

echo "✅ Stage 2 completed"

# Stage 3: Create .env and build Docker
echo "📋 Stage 3: Building application..."
expect << 'EOF'
set timeout 300
spawn ssh -o StrictHostKeyChecking=no root@103.136.69.249
expect "password:" { send "wBlO#rH6yDy2z0oB0J\r" }
expect "# " {
    send "cd /opt/ym-image-processor\r"
    expect "# "
    send "cat > .env << 'ENVEND'\nFAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5\nLORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors\nOPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw\nPORT=8080\nWEBHOOK_SECRET=ym-deploy-secret-2024\nENVEND\r"
    expect "# "
    send "docker build -t ym-processor .\r"
    expect "# "
    send "exit\r"
}
expect eof
EOF

echo "✅ Stage 3 completed"

# Stage 4: Run application
echo "📋 Stage 4: Starting application..."
expect << 'EOF'
set timeout 60
spawn ssh -o StrictHostKeyChecking=no root@103.136.69.249
expect "password:" { send "wBlO#rH6yDy2z0oB0J\r" }
expect "# " {
    send "cd /opt/ym-image-processor\r"
    expect "# "
    send "docker stop ym-processor 2>/dev/null || true\r"
    expect "# "
    send "docker rm ym-processor 2>/dev/null || true\r"
    expect "# "
    send "docker run -d --name ym-processor --restart always -p 8080:8080 --env-file .env ym-processor\r"
    expect "# "
    send "docker ps\r"
    expect "# "
    send "exit\r"
}
expect eof
EOF

echo "✅ Stage 4 completed"

echo ""
echo "🎉 Deployment completed!"
echo "Check application at: http://103.136.69.249:8080"