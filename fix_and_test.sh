#!/usr/bin/expect -f

# Comprehensive fix and test script
set timeout 60
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔧 FIXING AND TESTING OpenAI API..."

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

puts "🔑 Step 1: Checking current .env..."
send "cat .env | grep OPENAI\r"
expect "# "

puts "🔄 Step 2: Updating .env with correct key..."
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
send "# WORKING OPENAI KEY - Updated January 8, 2025\r"
expect "> "
send "OPENAI_API_KEY=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\r"
expect "> "
send "PORT=8080\r"
expect "> "
send "EOF\r"
expect "# "

puts "✅ Step 3: Verifying .env file..."
send "cat .env\r"
expect "# "

puts "🔄 Step 4: Rebuilding container with new environment..."
send "docker stop ym-processor\r"
expect "# "
send "docker rm ym-processor\r"
expect "# "

puts "🐳 Step 5: Starting fresh container..."
send "docker run -d --name ym-processor --restart always -p 8080:8080 --env-file .env ym-processor\r"
expect "# "

puts "⏳ Step 6: Waiting for container to fully start..."
send "sleep 15\r"
expect "# "

puts "🔍 Step 7: Checking container status..."
send "docker ps | grep ym-processor\r"
expect "ym-processor"
expect "# "

puts "📋 Step 8: Checking logs for errors..."
send "docker logs ym-processor --tail 10\r"
expect "# "

puts "🧪 Step 9: Testing health endpoint..."
send "curl -s http://localhost:8080/health | head -5\r"
expect "# "

puts "🧪 Step 10: Testing OpenAI API directly..."
send "docker exec ym-processor python3 -c \"
import os
import openai
try:
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.models.list()
    print('✅ OpenAI API works!')
    print(f'Models available: {len(response.data)}')
except Exception as e:
    print(f'❌ OpenAI API error: {e}')
\"\r"
expect "# "

puts "🧪 Step 11: Testing FAL API..."
send "docker exec ym-processor python3 -c \"
import os
import requests
try:
    headers = {'Authorization': f'Key {os.environ.get(\\\"FAL_KEY\\\")}'}
    response = requests.get('https://fal.run/status', headers=headers, timeout=10)
    print(f'✅ FAL API status: {response.status_code}')
except Exception as e:
    print(f'❌ FAL API error: {e}')
\"\r"
expect "# "

puts ""
puts "🎉 TESTING COMPLETE!"
puts "Now test the web interface at http://103.136.69.249:8080"

send "exit\r"
expect eof

puts "🏁 Fix and test completed"