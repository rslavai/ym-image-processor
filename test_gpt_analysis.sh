#!/usr/bin/expect -f

# Test GPT analysis on server
set timeout 30
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🧪 TESTING GPT ANALYSIS..."

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

puts "🧪 Step 1: Test GPT analyzer import..."
send "docker exec ym-processor python3 -c 'import sys; sys.path.append(\"/app/src\"); from processors.gpt_analyzer import GPTProductAnalyzer; print(\"GPT Analyzer imported successfully\")'\r"
expect "# "

puts "🔑 Step 2: Check OpenAI API key..."
send "docker exec ym-processor python3 -c 'import os; key = os.environ.get(\"OPENAI_API_KEY\", \"\"); print(f\"OpenAI key length: {len(key)} chars\"); print(f\"Key starts with: {key[:10] if key else \"NOT SET\"}...\")'\r"
expect "# "

puts "📊 Step 3: Test fallback analysis..."
send "docker exec ym-processor python3 -c '
import sys
sys.path.append(\"/app/src\")
from processors.gpt_analyzer import GPTProductAnalyzer
from PIL import Image

# Create test image
img = Image.new(\"RGB\", (300, 400), \"red\")
analyzer = GPTProductAnalyzer()
fallback = analyzer._get_fallback_analysis(img)
print(\"Fallback main_object_description:\", fallback.get(\"lora_optimization\", {}).get(\"main_object_description\", \"NOT FOUND\"))
print(\"Fallback type:\", fallback.get(\"product_identification\", {}).get(\"type\", \"NOT FOUND\"))
'\r"
expect "# "

puts "🧪 Step 4: Test create_lora_prompt with fallback..."
send "docker exec ym-processor python3 -c '
import sys
sys.path.append(\"/app/src\")
from processors.gpt_analyzer import GPTProductAnalyzer
from PIL import Image

img = Image.new(\"RGB\", (300, 400), \"red\")
analyzer = GPTProductAnalyzer()
fallback = analyzer._get_fallback_analysis(img)
prompt = analyzer.create_lora_prompt(fallback)
print(\"Generated prompt:\")
print(prompt)
'\r"
expect "# "

puts ""
puts "🔍 GPT ANALYSIS TEST COMPLETE"
puts "Check the results above to see if GPT is working or using fallback"

send "exit\r"
expect eof

puts "🏁 Test completed"