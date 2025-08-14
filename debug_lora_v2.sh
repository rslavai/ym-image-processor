#!/usr/bin/expect -f

# Debug LoRA V2 file
set timeout 30
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔍 DEBUG LoRA V2 FILE..."

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

puts "📄 Step 1: Check if file was actually copied..."
send "docker exec ym-processor stat /app/src/processors/batch_processor.py\r"
expect "# "

puts "🔍 Step 2: Search for ANY LoRA V2 mentions..."
send "docker exec ym-processor grep -n \"v2\" /app/src/processors/batch_processor.py | head -3\r"
expect "# "

puts "🔍 Step 3: Check the function signature..."
send "docker exec ym-processor grep -n \"_remove_background_fal_v2\" /app/src/processors/batch_processor.py\r"
expect "# "

puts "🔍 Step 4: Look for inference_steps parameter..."
send "docker exec ym-processor grep -n \"inference_steps = 50\" /app/src/processors/batch_processor.py\r"
expect "# "

puts "🔍 Step 5: Check current file size and modification time..."
send "docker exec ym-processor ls -la /app/src/processors/batch_processor.py\r"
expect "# "

puts "🔍 Step 6: Check last 10 lines of the function..."
send "docker exec ym-processor grep -A 10 \"lora_version == 'v2'\" /app/src/processors/batch_processor.py\r"
expect "# "

puts ""
puts "🔍 DEBUG COMPLETE - Check the results above"

send "exit\r"
expect eof

puts "🏁 Debug completed"