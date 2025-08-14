#!/usr/bin/expect -f

# Simple GPT test
set timeout 30
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🧪 SIMPLE GPT TEST..."

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

puts "🔑 Check OpenAI key..."
send "docker exec ym-processor python3 -c 'import os; print(\"OpenAI key set:\", bool(os.environ.get(\"OPENAI_API_KEY\")))'\r"
expect "# "

puts "📋 Check fallback analysis..."
send "docker exec ym-processor python3 -c 'import sys; sys.path.append(\"/app/src\"); from processors.gpt_analyzer import GPTProductAnalyzer; from PIL import Image; analyzer = GPTProductAnalyzer(); img = Image.new(\"RGB\", (300, 400), \"red\"); fallback = analyzer._get_fallback_analysis(img); print(\"Main object:\", fallback[\"lora_optimization\"][\"main_object_description\"])'\r"
expect "# "

puts ""
puts "✅ Simple test complete"

send "exit\r"
expect eof

puts "🏁 Done"