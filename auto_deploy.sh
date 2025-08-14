#!/usr/bin/expect -f

# Automatic deployment script using expect
# Handles password authentication automatically

set timeout 30
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🚀 Starting automatic deployment to $server_ip"

# SSH to server
spawn ssh -o StrictHostKeyChecking=no $username@$server_ip

# Handle password prompt
expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "# " {
        puts "✅ Connected successfully"
    }
    timeout {
        puts "❌ Connection timeout"
        exit 1
    }
}

# Send deployment commands
puts "📦 Updating repository..."
send "cd /opt/ym-image-processor\r"
expect "# "

send "git pull origin main\r"
expect {
    "# " {
        puts "✅ Git pull successful"
    }
    "error:" {
        puts "⚠️ Git pull failed, trying reset..."
        send "git fetch --all\r"
        expect "# "
        send "git reset --hard origin/main\r"
        expect "# "
    }
}

puts "🔧 Creating .env file..."
send "cat > .env << 'EOF'\r"
expect "> "
send "# Официальный ключ для fal_client\r"
expect "> "
send "FAL_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5\r"
expect "> "
send "# Резервный ключ для совместимости\r"
expect "> "
send "FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5\r"
expect "> "
send "LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors\r"
expect "> "
send "OPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw\r"
expect "> "
send "PORT=8080\r"
expect "> "
send "EOF\r"
expect "# "

puts "🐳 Building Docker image..."
send "docker build -t ym-processor .\r"
expect {
    "Successfully tagged ym-processor:latest" {
        puts "✅ Docker build successful"
        expect "# "
    }
    "# " {
        puts "✅ Docker build completed"
    }
    timeout {
        puts "⚠️ Docker build taking longer than expected..."
        expect "# "
    }
}

puts "🔄 Restarting container..."
send "docker stop ym-processor 2>/dev/null || true\r"
expect "# "
send "docker rm ym-processor 2>/dev/null || true\r"
expect "# "

send "docker run -d --name ym-processor --restart always -p 8080:8080 --env-file .env ym-processor\r"
expect "# "

puts "⏳ Waiting for container to start..."
send "sleep 10\r"
expect "# "

puts "🔍 Checking container status..."
send "docker ps | grep ym-processor\r"
expect {
    "ym-processor" {
        puts "✅ Container is running!"
        expect "# "
        
        puts "📋 Container logs:"
        send "docker logs --tail 20 ym-processor\r"
        expect "# "
        
        puts ""
        puts "🎉 DEPLOYMENT SUCCESSFUL!"
        puts "✅ LoRA V2 fixes deployed"
        puts "✅ fal-client updated"
        puts "✅ Environment variables configured"
        puts ""
        puts "🌐 Service URL: http://103.136.69.249:8080"
    }
    "# " {
        puts "❌ Container not found in running processes"
        send "docker logs ym-processor\r"
        expect "# "
    }
}

# Exit
send "exit\r"
expect eof

puts "🏁 Deployment script completed"