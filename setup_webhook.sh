#!/bin/bash
# Setup webhook server for auto-deployment

echo "🔧 Setting up webhook server..."

expect << 'EOF'
set timeout 60
spawn ssh -o StrictHostKeyChecking=no root@103.136.69.249
expect "password:" { send "wBlO#rH6yDy2z0oB0J\r" }
expect "# " {
    send "cd /opt/ym-image-processor\r"
    expect "# "
    send "pip3 install flask requests\r"
    expect "# "
    send "cat > /etc/systemd/system/ym-webhook.service << 'SERVICEEND'\n[Unit]\nDescription=YM Image Processor Webhook Server\nAfter=network.target\n\n[Service]\nType=simple\nUser=root\nWorkingDirectory=/opt/ym-image-processor\nEnvironment=\"WEBHOOK_SECRET=ym-deploy-secret-2024\"\nExecStart=/usr/bin/python3 /opt/ym-image-processor/webhook_server.py\nRestart=always\nRestartSec=3\n\n[Install]\nWantedBy=multi-user.target\nSERVICEEND\r"
    expect "# "
    send "systemctl daemon-reload\r"
    expect "# "
    send "systemctl enable ym-webhook\r"
    expect "# "
    send "systemctl start ym-webhook\r"
    expect "# "
    send "ufw allow 9000/tcp\r"
    expect "# "
    send "systemctl status ym-webhook --no-pager -l\r"
    expect "# "
    send "exit\r"
}
expect eof
EOF

echo "✅ Webhook setup completed"

# Test webhook
echo "🔍 Testing webhook..."
sleep 5
curl -s http://103.136.69.249:9000/health && echo "✅ Webhook is working!" || echo "❌ Webhook test failed"

echo ""
echo "🎉 Setup completed!"
echo "Application: http://103.136.69.249:8080"
echo "Webhook: http://103.136.69.249:9000/webhook"