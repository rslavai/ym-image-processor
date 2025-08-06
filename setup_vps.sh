#!/bin/bash

# Скрипт установки для Ubuntu 24.04 VPS
# Запускать от root пользователя

echo "==================================="
echo "🚀 Установка YM Image Processor"
echo "==================================="

# 1. Обновление системы
echo "📦 Обновление пакетов..."
apt update && apt upgrade -y

# 2. Установка необходимых пакетов
echo "🔧 Установка зависимостей..."
apt install -y curl git nginx certbot python3-certbot-nginx ufw

# 3. Установка Docker
echo "🐳 Установка Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# 4. Клонирование репозитория
echo "📥 Клонирование репозитория..."
cd /opt
git clone https://github.com/rslavai/ym-image-processor.git
cd ym-image-processor

# 5. Создание файла переменных окружения
echo "🔑 Настройка переменных окружения..."
cat > .env << EOF
FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5
LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors
PORT=8080
EOF

# 6. Сборка Docker образа
echo "🏗️ Сборка Docker образа..."
docker build -t ym-processor .

# 7. Запуск контейнера
echo "▶️ Запуск приложения..."
docker run -d \
  --name ym-processor \
  --restart always \
  -p 8080:8080 \
  --env-file .env \
  ym-processor

# 8. Настройка файрвола
echo "🔒 Настройка файрвола..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw allow 8080
ufw --force enable

# 9. Настройка Nginx
echo "🌐 Настройка Nginx..."
cat > /etc/nginx/sites-available/ym-processor << 'NGINX'
server {
    listen 80;
    server_name 103.136.69.249;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -s /etc/nginx/sites-available/ym-processor /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 10. Создание скрипта обновления
echo "📝 Создание скрипта обновления..."
cat > /opt/update-app.sh << 'UPDATE'
#!/bin/bash
cd /opt/ym-image-processor
git pull
docker build -t ym-processor .
docker stop ym-processor
docker rm ym-processor
docker run -d \
  --name ym-processor \
  --restart always \
  -p 8080:8080 \
  --env-file .env \
  ym-processor
UPDATE

chmod +x /opt/update-app.sh

echo "==================================="
echo "✅ Установка завершена!"
echo "==================================="
echo ""
echo "📱 Ваше приложение доступно по адресу:"
echo "   http://103.136.69.249"
echo ""
echo "🔄 Для обновления используйте:"
echo "   /opt/update-app.sh"
echo ""
echo "📊 Просмотр логов:"
echo "   docker logs ym-processor"
echo ""
echo "==================================="