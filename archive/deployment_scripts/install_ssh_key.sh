#!/bin/bash
# Install SSH key for passwordless authentication

PUBLIC_KEY=$(cat ~/.ssh/ym_server_key.pub)

echo "🔑 Installing SSH key for passwordless access..."

expect << EOF
set timeout 30
spawn ssh -o StrictHostKeyChecking=no root@103.136.69.249
expect "password:" { send "wBlO#rH6yDy2z0oB0J\r" }
expect "# " {
    send "mkdir -p ~/.ssh\r"
    expect "# "
    send "chmod 700 ~/.ssh\r"
    expect "# "
    send "echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys\r"
    expect "# "
    send "chmod 600 ~/.ssh/authorized_keys\r"
    expect "# "
    send "sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.tmp\r"
    expect "# "
    send "mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys\r"
    expect "# "
    send "echo 'SSH key installed successfully'\r"
    expect "# "
    send "exit\r"
}
expect eof
EOF

echo "✅ SSH key installation completed"

# Test the key
echo "🔍 Testing SSH key authentication..."
if ssh -i ~/.ssh/ym_server_key -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@103.136.69.249 "echo 'SSH key works!'" 2>/dev/null; then
    echo "✅ SSH key authentication successful!"
    
    # Create SSH config for easy access
    echo "📝 Creating SSH config..."
    cat >> ~/.ssh/config << 'SSHCONFIG'

# YM Image Processor Server
Host ym-server
    HostName 103.136.69.249
    User root
    IdentityFile ~/.ssh/ym_server_key
    StrictHostKeyChecking no
SSHCONFIG
    
    echo "✅ SSH config created. Now you can use: ssh ym-server"
    
else
    echo "❌ SSH key authentication failed"
    exit 1
fi