#!/bin/bash
# Automated deployment script using expect

SERVER_IP="103.136.69.249"
SERVER_USER="root"
SERVER_PASSWORD="wBlO#rH6yDy2z0oB0J"

echo "🚀 Starting automated deployment to $SERVER_IP"

# Create expect script for automated SSH
cat > /tmp/deploy_commands.exp << 'EOF'
#!/usr/bin/expect -f

set timeout 300
set server_ip [lindex $argv 0]
set server_user [lindex $argv 1]  
set server_password [lindex $argv 2]

spawn ssh -o StrictHostKeyChecking=no $server_user@$server_ip

expect {
    "password:" {
        send "$server_password\r"
        exp_continue
    }
    "$ " {
        # We're logged in, start deployment
        send "echo '🔧 Starting YM Image Processor deployment...'\r"
        expect "$ "
        
        # Install packages
        send "apt-get update && apt-get install -y git docker.io python3 python3-pip curl ufw\r"
        expect "$ " { send "\r" }
        expect "$ "
        
        # Start Docker
        send "systemctl start docker && systemctl enable docker\r"
        expect "$ "
        
        # Setup project
        send "mkdir -p /opt/ym-image-processor && cd /opt\r"
        expect "$ "
        
        # Clone/update repository
        send "if \[ -d \"ym-image-processor/.git\" \]; then echo \"Updating repo...\"; cd ym-image-processor; git pull origin main || (git fetch --all && git reset --hard origin/main); else echo \"Cloning repo...\"; git clone https://github.com/rslavai/ym-image-processor.git; cd ym-image-processor; fi\r"
        expect "$ "
        
        # Create .env file
        send "cat > .env << 'ENVEOF'\r"
        send "FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5\r"
        send "LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors\r"
        send "OPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw\r"
        send "PORT=8080\r"
        send "WEBHOOK_SECRET=ym-deploy-secret-2024\r"
        send "ENVEOF\r"
        expect "$ "
        
        # Build and start application
        send "docker stop ym-processor 2>/dev/null || true\r"
        expect "$ "
        send "docker rm ym-processor 2>/dev/null || true\r"
        expect "$ "
        send "echo 'Building Docker image...'\r"
        expect "$ "
        send "docker build -t ym-processor .\r"
        expect "$ "
        send "echo 'Starting container...'\r"
        expect "$ "
        send "docker run -d --name ym-processor --restart always -p 8080:8080 --env-file .env ym-processor\r"
        expect "$ "
        
        # Setup webhook
        send "pip3 install flask requests\r"
        expect "$ "
        
        # Create systemd service
        send "cat > /etc/systemd/system/ym-webhook.service << 'SERVICEEOF'\r"
        send "\[Unit\]\r"
        send "Description=YM Image Processor Webhook Server\r"
        send "After=network.target\r"
        send "\r"
        send "\[Service\]\r"
        send "Type=simple\r"
        send "User=root\r"
        send "WorkingDirectory=/opt/ym-image-processor\r"
        send "Environment=\"WEBHOOK_SECRET=ym-deploy-secret-2024\"\r"
        send "ExecStart=/usr/bin/python3 /opt/ym-image-processor/webhook_server.py\r"
        send "Restart=always\r"
        send "RestartSec=3\r"
        send "\r"
        send "\[Install\]\r"
        send "WantedBy=multi-user.target\r"
        send "SERVICEEOF\r"
        expect "$ "
        
        # Start webhook service
        send "systemctl daemon-reload && systemctl enable ym-webhook && systemctl start ym-webhook\r"
        expect "$ "
        
        # Configure firewall
        send "ufw --force enable && ufw allow 22/tcp && ufw allow 8080/tcp && ufw allow 9000/tcp\r"
        expect "$ "
        
        # Check status
        send "echo '🔍 Checking status...'\r"
        expect "$ "
        send "docker ps | grep ym-processor\r"
        expect "$ "
        send "systemctl status ym-webhook --no-pager -l\r"
        expect "$ "
        
        send "echo '✅ Deployment completed!'\r"
        send "echo 'Application: http://103.136.69.249:8080'\r"
        send "echo 'Webhook: http://103.136.69.249:9000/webhook'\r"
        expect "$ "
        
        send "exit\r"
        expect eof
    }
    timeout {
        puts "Connection timeout"
        exit 1
    }
}
EOF

# Check if expect is available
if ! command -v expect &> /dev/null; then
    echo "Installing expect..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Try different package managers for macOS
        if command -v brew &> /dev/null; then
            brew install expect
        elif command -v port &> /dev/null; then
            sudo port install expect
        else
            echo "❌ Please install expect manually:"
            echo "   brew install expect  # with Homebrew"
            echo "   or"
            echo "   sudo port install expect  # with MacPorts"
            exit 1
        fi
    else
        sudo apt-get update && sudo apt-get install -y expect
    fi
fi

# Make expect script executable and run it
chmod +x /tmp/deploy_commands.exp
/tmp/deploy_commands.exp "$SERVER_IP" "$SERVER_USER" "$SERVER_PASSWORD"

# Cleanup
rm -f /tmp/deploy_commands.exp

echo ""
echo "🎉 Deployment script completed!"
echo "Check the output above for any errors."