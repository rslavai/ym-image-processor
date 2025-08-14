#!/usr/bin/expect -f

# Fix OpenAI version conflict
set timeout 60
set server_ip "103.136.69.249"
set username "root"
set password "wBlO#rH6yDy2z0oB0J"

puts "🔧 FIXING OpenAI version conflict..."

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

puts "📦 Step 1: Checking current OpenAI version..."
send "docker exec ym-processor pip list | grep openai\r"
expect "# "

puts "🔄 Step 2: Updating requirements.txt..."
send "cat > requirements.txt << 'EOF'\r"
expect "> "
send "# Core dependencies\r"
expect "> "
send "Flask==3.0.0\r"
expect "> "
send "Pillow==10.1.0\r"
expect "> "
send "requests==2.31.0\r"
expect "> "
send "numpy==1.24.3\r"
expect "> "
send "openai==1.52.0\r"
expect "> "
send "gunicorn==21.2.0\r"
expect "> "
send "fal-client==0.3.0\r"
expect "> "
send "EOF\r"
expect "# "

puts "🐳 Step 3: Rebuilding Docker image with fixed dependencies..."
send "docker build -t ym-processor .\r"
expect {
    "Successfully tagged" {
        puts "✅ Build successful"
        expect "# "
    }
    "# " {
        puts "✅ Build completed"
    }
    timeout {
        puts "⚠️ Build taking longer..."
        expect "# "
    }
}

puts "🔄 Step 4: Restarting with new image..."
send "docker stop ym-processor && docker rm ym-processor\r"
expect "# "

send "docker run -d --name ym-processor --restart always -p 8080:8080 --env-file .env ym-processor\r"
expect "# "

puts "⏳ Step 5: Waiting for startup..."
send "sleep 20\r"
expect "# "

puts "🧪 Step 6: Testing OpenAI API again..."
send "docker exec ym-processor python3 -c \"
import os
import openai
try:
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    models = client.models.list()
    print('✅ OpenAI API works perfectly!')
    print(f'Available models: {len(models.data)}')
    # Test a simple call
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': 'Hello'}],
        max_tokens=5
    )
    print('✅ Chat API also works!')
except Exception as e:
    print(f'❌ OpenAI API error: {e}')
\"\r"
expect "# "

puts "🔍 Step 7: Checking service health..."
send "curl -s http://localhost:8080/health\r"
expect "# "

puts "📋 Step 8: Checking logs..."
send "docker logs ym-processor --tail 5\r"
expect "# "

puts ""
puts "🎉 ALL TESTS COMPLETE!"
puts "✅ OpenAI API should now work properly"
puts "✅ Service is ready for testing"

send "exit\r"
expect eof

puts "🏁 OpenAI fix completed successfully"