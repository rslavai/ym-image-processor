#!/usr/bin/expect -f

# Monitor live logs for LoRA prompt
set timeout 300
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔴 LIVE LOG MONITORING..."
puts "⚡ Start processing an image NOW in the web interface!"
puts "📱 Go to: http://103.136.69.249:8080"
puts ""

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

puts "📡 Starting live log monitoring..."
puts "🚨 Upload an image and process it NOW!"
puts ""

send "docker logs -f ym-processor\r"

expect {
    -timeout 120
    -re ".*API.*" {
        puts "\n🎯 FOUND API ACTIVITY!"
        exp_continue
    }
    -re ".*prompt.*" {
        puts "\n🎯 FOUND PROMPT!"
        exp_continue
    }
    -re ".*POST.*process_single.*" {
        puts "\n🎯 PROCESSING REQUEST DETECTED!"
        exp_continue
    }
    timeout {
        puts "\n⏰ No activity detected in 2 minutes"
    }
}

send "\003"
expect "# "

send "exit\r"
expect eof

puts "🏁 Live monitoring completed"