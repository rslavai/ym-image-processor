#!/usr/bin/expect -f

# Fix LoRA V2 parameters directly on server
set timeout 30
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔧 FIXING LoRA V2 PARAMETERS DIRECTLY..."

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

puts "🔧 Step 1: Fix inference_steps from 1000 to 50..."
send "docker exec ym-processor sed -i 's/inference_steps = 1000/inference_steps = 50  # Максимум для FLUX Kontext API (не для обучения!)/' /app/src/processors/batch_processor.py\r"
expect "# "

puts "🔧 Step 2: Fix guidance_scale from 0.0001 to 3.5..."
send "docker exec ym-processor sed -i 's/guidance_scale = 0.0001  # learning_rate from config/guidance_scale = 3.5  # Правильное значение для guidance_scale (не learning_rate!)/' /app/src/processors/batch_processor.py\r"
expect "# "

puts "✅ Step 3: Verify the fixes..."
send "docker exec ym-processor grep -A 3 \"lora_version == 'v2'\" /app/src/processors/batch_processor.py\r"
expect "# "

puts "🔄 Step 4: Restart container to reload the code..."
send "docker restart ym-processor\r"
expect "# "

puts "⏳ Step 5: Wait for restart..."
send "sleep 10\r"
expect "# "

puts "🔍 Step 6: Final verification..."
send "curl -s http://localhost:8080/health\r"
expect "# "

puts "🧪 Step 7: Check the fixed parameters..."
send "docker exec ym-processor grep -A 5 \"lora_version == 'v2'\" /app/src/processors/batch_processor.py\r"
expect "# "

puts ""
puts "🎉 LoRA V2 PARAMETERS FIXED!"
puts "✅ inference_steps: 1000 → 50"
puts "✅ guidance_scale: 0.0001 → 3.5"
puts "✅ Container restarted"
puts "✅ Ready for LoRA V2 testing"

send "exit\r"
expect eof

puts "🏁 LoRA V2 parameters fixed successfully"