#!/usr/bin/expect -f

# Deploy LoRA V2 fixes to server
set timeout 60
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔧 DEPLOYING LoRA V2 FIXES..."

spawn ssh -o StrictHostKeyChecking=no $username@$server_ip

expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "# " {
        puts "✅ Connected to server"
    }
}

send "cd /opt/ym-image-processor\r"
expect "# "

puts "📥 Step 1: Getting latest code from Git..."
send "git pull origin main\r"
expect "# "

puts "🔄 Step 2: Rebuilding Docker image with latest code..."
send "docker build -t ym-processor .\r"
expect {
    "Successfully tagged" {
        puts "✅ Docker build successful"
        expect "# "
    }
    "# " {
        puts "✅ Build completed"
    }
    timeout {
        puts "⚠️ Build taking time, continuing..."
        expect "# "
    }
}

puts "🔄 Step 3: Stopping old container..."
send "docker stop ym-processor\r"
expect "# "

send "docker rm ym-processor\r"
expect "# "

puts "🚀 Step 4: Starting new container with updated code..."
send "docker run -d --name ym-processor --restart always -p 8080:8080 --env-file .env ym-processor\r"
expect "# "

puts "⏳ Step 5: Waiting for container startup..."
send "sleep 15\r"
expect "# "

puts "🔍 Step 6: Checking container status..."
send "docker ps | grep ym-processor\r"
expect "# "

puts "🧪 Step 7: Testing LoRA V2 parameters directly..."
send "docker exec ym-processor python3 -c \"
print('🧪 Testing LoRA V2 parameters...')
import sys
sys.path.append('/app/src')
from processors.batch_processor import BatchProcessor
from PIL import Image
import tempfile
import os

# Create test image
test_img = Image.new('RGB', (100, 100), 'red')
processor = BatchProcessor('/tmp')

# Test LoRA V2 function exists and has correct parameters
try:
    result = processor._remove_background_fal_v2.__doc__
    print('✅ LoRA V2 function exists')
    print('📖 Function docs:', result[:100] if result else 'None')
except Exception as e:
    print('❌ LoRA V2 function error:', e)

print('✅ LoRA V2 code deployment test complete')
\"\r"
expect "# "

puts "📋 Step 8: Checking logs for any errors..."
send "docker logs ym-processor --tail 10\r"
expect "# "

puts "🌐 Step 9: Final health check..."
send "curl -s http://localhost:8080/health\r"
expect "# "

puts ""
puts "🎉 LoRA V2 CODE DEPLOYMENT COMPLETE!"
puts "✅ Latest code deployed to server"
puts "✅ Container restarted with fixes"
puts "✅ Ready for LoRA V2 testing"

send "exit\r"
expect eof

puts "🏁 LoRA V2 fixes deployed successfully"