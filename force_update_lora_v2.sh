#!/usr/bin/expect -f

# Force update LoRA V2 code on server
set timeout 60
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔧 FORCE UPDATING LoRA V2 CODE..."

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

puts "🔍 Step 1: Check current LoRA V2 parameters..."
send "docker exec ym-processor grep -A 5 -B 5 \"lora_version == 'v2'\" /app/src/processors/batch_processor.py\r"
expect "# "

puts "🔄 Step 2: Copy updated file directly to container..."
send "docker cp src/processors/batch_processor.py ym-processor:/app/src/processors/batch_processor.py\r"
expect "# "

puts "✅ Step 3: Verify the copy worked..."
send "docker exec ym-processor grep -n \"guidance_scale = 3.5\" /app/src/processors/batch_processor.py\r"
expect "# "

puts "🔄 Step 4: Restart container to reload code..."
send "docker restart ym-processor\r"
expect "# "

puts "⏳ Step 5: Wait for restart..."
send "sleep 10\r"
expect "# "

puts "🔍 Step 6: Verify service is healthy..."
send "curl -s http://localhost:8080/health\r"
expect "# "

puts "🧪 Step 7: Final verification of LoRA V2 parameters..."
send "docker exec ym-processor grep -A 3 \"guidance_scale = 3.5\" /app/src/processors/batch_processor.py\r"
expect "# "

puts ""
puts "🎉 LoRA V2 CODE FORCE UPDATE COMPLETE!"
puts "✅ Updated code copied to container"
puts "✅ Container restarted"
puts "✅ Ready for LoRA V2 testing"

send "exit\r"
expect eof

puts "🏁 Force update completed"