#!/bin/bash
# Script to setup SSH key and deploy system on server

SERVER_IP="103.136.69.249"
SERVER_USER="root"
SERVER_PASSWORD="wBlO#rH6yDy2z0oB0J"
SSH_KEY_PATH="$HOME/.ssh/ym_server_key"
PUBLIC_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQD8n9y3Fei1Tz2WwDuBmOdj9/tg80/kIAZLynKWX+VjBLx9jV4HcQhWamnux7tdVkrEPDxhYBIlSO9+TmSYw8fE6+psrFkmzrHGI/pQB3giOs4NDq9ZndfYHQsvpKRlXYmj+bipF1xucHtfjHrIIBv4MSifIXOw+eSGMwpNSycsI8QyeOV1eUqa2ff121WlP0v4pcF9RZGz0ycxrAsj4ghZOEnUcUcM9MRaeb6gcWf0iNruWKhYizHZ46FKv3x8AH5sOnY/aAyqUHJSm6c0eYRE8k2IBmc7kObadct3103y8MNsUzpmW50chm7Q+c1s0dQMKoToNfvX95EKF/NRwD/dELbl4Lxf4XPHzBRs97tHvLPpFZ3q+2pbf0Mg+tZzlYNOeKTmOSlo5Bv57t2H2SYsVvUhvM3nlHdqeyycI8MNkcezyaxRnBcp927606TkDGKm+zGYQ2vjmfGe1cor7uqu3591usatw8Ajj+mokrWKjcdm+IgVRNBK1orkFnej9SIrkDYeQuhZ9JRHRd3QcQeLgQvTkV+EPpg/PH4oOWFEEqJsEC15PyVMvc93PAkJpYvqBHNs+/jM49U5zROPSkDsQwhywTaOgMVVZDoqLFD9YIVFOlFcIc/u1UTwIiOga0twc0ClTOYzmebgnwJ1T5A/3OkXINycjjmUNXHbzB8gHQ== shorstov@i115095471"

echo "🚀 Setting up SSH key and deploy system on server $SERVER_IP"

# Function to execute commands on remote server
remote_exec() {
    echo "Executing: $1"
    expect -c "
        spawn ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP \"$1\"
        expect \"password:\"
        send \"$SERVER_PASSWORD\r\"
        expect eof
    "
}

# Check if expect is installed
if ! command -v expect &> /dev/null; then
    echo "Installing expect for automated SSH..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        xcode-select --install 2>/dev/null || true
        if command -v port &> /dev/null; then
            sudo port install expect
        else
            echo "Please install expect manually: brew install expect"
            exit 1
        fi
    else
        # Linux
        sudo apt-get update && sudo apt-get install -y expect
    fi
fi

echo "📋 Step 1: Setting up SSH key..."
remote_exec "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
remote_exec "echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
remote_exec "sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.tmp && mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys"

echo "✅ SSH key installed. Testing connection..."
ssh -i $SSH_KEY_PATH -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "echo 'SSH key authentication successful!'" || {
    echo "❌ SSH key authentication failed"
    exit 1
}

echo "📋 Step 2: Setting up project directory..."
ssh -i $SSH_KEY_PATH $SERVER_USER@$SERVER_IP << 'ENDSSH'
# Create project directory
mkdir -p /opt/ym-image-processor
cd /opt

# Clone or update repository
if [ -d "ym-image-processor/.git" ]; then
    echo "Repository exists, updating..."
    cd ym-image-processor
    git pull origin main
else
    echo "Cloning repository..."
    git clone https://github.com/rslavai/ym-image-processor.git || {
        rm -rf ym-image-processor
        git clone https://github.com/rslavai/ym-image-processor.git
    }
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

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

echo "✅ Project setup completed"
ENDSSH

echo "📋 Step 3: Building and starting application..."
ssh -i $SSH_KEY_PATH $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /opt/ym-image-processor

# Stop existing container
docker stop ym-processor 2>/dev/null || true
docker rm ym-processor 2>/dev/null || true

# Build new image
echo "Building Docker image..."
docker build -t ym-processor .

# Start container
echo "Starting container..."
docker run -d \
    --name ym-processor \
    --restart always \
    -p 8080:8080 \
    --env-file .env \
    ym-processor

# Wait and check
sleep 10
if docker ps | grep -q ym-processor; then
    echo "✅ Container started successfully"
    docker logs --tail 10 ym-processor
else
    echo "❌ Container failed to start"
    docker logs ym-processor
    exit 1
fi
ENDSSH

echo "📋 Step 4: Setting up webhook for auto-deploy..."
ssh -i $SSH_KEY_PATH $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /opt/ym-image-processor

# Install Python dependencies for webhook server
apt-get update
apt-get install -y python3 python3-pip

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

# Start and enable webhook service
systemctl daemon-reload
systemctl enable ym-webhook
systemctl start ym-webhook

# Check webhook status
sleep 3
if systemctl is-active --quiet ym-webhook; then
    echo "✅ Webhook server started successfully"
else
    echo "❌ Webhook server failed to start"
    systemctl status ym-webhook
fi

# Open firewall ports
ufw allow 8080/tcp
ufw allow 9000/tcp

echo "🎉 Server setup completed!"
echo "Application: http://103.136.69.249:8080"
echo "Webhook: http://103.136.69.249:9000/webhook"
ENDSSH

echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Test application: http://103.136.69.249:8080"
echo "2. Setup GitHub webhook: http://103.136.69.249:9000/webhook"
echo "3. Use secret: ym-deploy-secret-2024"