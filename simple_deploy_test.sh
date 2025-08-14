#!/usr/bin/expect -f

# Simple deployment test
set timeout 30
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔧 SIMPLE LoRA V2 TEST..."

spawn ssh -o StrictHostKeyChecking=no $username@$server_ip

expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "# " {
        puts "✅ Connected"
    }
}

send "cd /opt/ym-image-processor\r"
expect "# "

puts "🔍 Step 1: Check current container status..."
send "docker ps | grep ym-processor\r"
expect "# "

puts "📋 Step 2: Check service health..."
send "curl -s http://localhost:8080/health\r"
expect "# "

puts "🧪 Step 3: Test LoRA V2 function exists..."
send "docker exec ym-processor python3 -c 'import sys; sys.path.append(\"/app/src\"); from processors.batch_processor import BatchProcessor; print(\"LoRA V2 function exists:\", hasattr(BatchProcessor, \"_remove_background_fal_v2\"))'\r"
expect "# "

puts "📄 Step 4: Check batch_processor.py file exists..."
send "docker exec ym-processor ls -la /app/src/processors/batch_processor.py\r"
expect "# "

puts "🔍 Step 5: Check LoRA V2 parameters in file..."
send "docker exec ym-processor grep -n \"guidance_scale = 3.5\" /app/src/processors/batch_processor.py\r"
expect "# "

puts "📊 Step 6: Check logs for startup..."
send "docker logs ym-processor --tail 5\r"
expect "# "

puts ""
puts "🎉 SIMPLE TEST COMPLETE!"
puts "Now you can test LoRA V2 through the web interface"

send "exit\r"
expect eof

puts "🏁 Simple test completed"