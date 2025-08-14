#!/usr/bin/expect -f

# Check service status
set timeout 30
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔍 CHECKING SERVICE STATUS..."

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

puts "📊 Step 1: Check Docker containers..."
send "docker ps -a | grep ym-processor\r"
expect "# "

puts "🔍 Step 2: Check if container is running..."
send "docker ps | grep ym-processor\r"
expect "# "

puts "📋 Step 3: Check container logs..."
send "docker logs ym-processor --tail 20\r"
expect "# "

puts "🌐 Step 4: Check port binding..."
send "netstat -tlnp | grep 8080\r"
expect "# "

puts "🔧 Step 5: Check Docker daemon..."
send "docker info | head -5\r"
expect "# "

puts "💾 Step 6: Check disk space..."
send "df -h | head -5\r"
expect "# "

puts "🔄 Step 7: Check system resources..."
send "free -h\r"
expect "# "

puts ""
puts "📊 SERVICE STATUS CHECK COMPLETE"

send "exit\r"
expect eof

puts "🏁 Status check completed"