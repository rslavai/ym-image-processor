#!/usr/bin/expect -f

# Final comprehensive test
set timeout 30
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔧 FINAL TEST OF EVERYTHING..."

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

puts "🔍 Step 1: Check if container is running..."
send "docker ps | grep ym-processor\r"
expect "# "

puts "📋 Step 2: Check service health..."
send "curl -s http://localhost:8080/health\r"
expect "# "

puts "🧪 Step 3: Simple OpenAI test..."
send "docker exec ym-processor python3 -c 'import openai; print(\"OpenAI imported successfully\")'\r"
expect "# "

puts "🧪 Step 4: Test environment variables..."
send "docker exec ym-processor python3 -c 'import os; print(\"OPENAI_API_KEY:\", \"SET\" if os.environ.get(\"OPENAI_API_KEY\") else \"NOT SET\")'\r"
expect "# "

puts "🧪 Step 5: Test FAL client..."
send "docker exec ym-processor python3 -c 'import fal_client; print(\"fal_client imported successfully\")'\r"
expect "# "

puts "📊 Step 6: Check logs for errors..."
send "docker logs ym-processor --tail 15 | grep -i error || echo 'No errors found'\r"
expect "# "

puts ""
puts "🎉 COMPREHENSIVE TEST COMPLETE!"
puts "🌐 Web interface: http://103.136.69.249:8080"
puts "📊 Health check: http://103.136.69.249:8080/health"

send "exit\r"
expect eof

puts "🏁 All tests completed"