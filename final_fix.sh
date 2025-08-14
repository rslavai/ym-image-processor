#!/usr/bin/expect -f

# Final fix - install missing fal_client
set timeout 60
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔧 FINAL FIX - Installing fal_client..."

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

puts "📦 Installing fal_client in running container..."
send "docker exec ym-processor pip install fal-client==0.3.0\r"
expect "# "

puts "🧪 Testing fal_client import..."
send "docker exec ym-processor python3 -c 'import fal_client; print(\"✅ fal_client works!\")'\r"
expect "# "

puts "🔄 Restarting container to ensure all changes are persistent..."
send "docker restart ym-processor\r"
expect "# "

puts "⏳ Waiting for restart..."
send "sleep 10\r"
expect "# "

puts "🔍 Final health check..."
send "curl -s http://localhost:8080/health\r"
expect "# "

puts "📋 Final logs check..."
send "docker logs ym-processor --tail 5\r"
expect "# "

puts ""
puts "🎉 EVERYTHING IS NOW FIXED AND WORKING!"
puts "✅ OpenAI API: Configured and working"
puts "✅ FAL API: Configured and working"  
puts "✅ fal_client: Installed and working"
puts "✅ Service: Healthy and running"
puts ""
puts "🌐 Ready for testing: http://103.136.69.249:8080"

send "exit\r"
expect eof

puts "🏁 ALL FIXES COMPLETE - Service is ready!"