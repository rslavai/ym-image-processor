# 🚀 Руководство по развертыванию

## 📋 Требования к системе

### Минимальные требования
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: 4 GB (рекомендуется 8 GB)
- **CPU**: 2 cores (рекомендуется 4 cores)
- **Диск**: 20 GB свободного места
- **Сеть**: Стабильное интернет-соединение

### Программное обеспечение
- **Docker**: 20.10+
- **Python**: 3.9+ (для локальной разработки)
- **Git**: Для клонирования репозитория
- **SSH**: Для удаленного управления

## 🔑 Подготовка API ключей

### 1. OpenAI API ключ
1. Зайдите на https://platform.openai.com/api-keys
2. Создайте новый API ключ
3. Сохраните его в безопасном месте

### 2. fal.ai API ключ  
1. Зайдите на https://fal.ai/dashboard
2. Получите API ключ
3. Убедитесь, что у вас есть доступ к FLUX Kontext

### 3. LoRA модели
- **V1**: `https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors`
- **V2**: `https://v3.fal.media/files/zebra/KoeQj8N4bU6OGnPT2VABy_adapter_model.safetensors`

## 🐳 Docker развертывание (Рекомендуется)

### Быстрый старт

1. **Клонирование репозитория**
```bash
git clone https://github.com/rslavai/ym-image-processor.git
cd ym-image-processor
```

2. **Создание .env файла**
```bash
cat > .env << 'EOF'
FAL_KEY=your_fal_api_key_here
FAL_API_KEY=your_fal_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors
PORT=8080
EOF
```

3. **Сборка и запуск**
```bash
docker build -t ym-processor .
docker run -d \
  --name ym-processor \
  --restart always \
  -p 8080:8080 \
  --env-file .env \
  ym-processor
```

4. **Проверка работы**
```bash
docker ps | grep ym-processor
docker logs ym-processor --tail 20
```

### Production развертывание

#### С nginx (рекомендуется)
```bash
# Установка nginx
sudo apt update && sudo apt install nginx

# Копирование конфигурации
sudo cp config/nginx.conf /etc/nginx/sites-available/ym-processor
sudo ln -s /etc/nginx/sites-available/ym-processor /etc/nginx/sites-enabled/
sudo systemctl reload nginx

# Запуск с проксированием
docker run -d \
  --name ym-processor \
  --restart always \
  -p 127.0.0.1:8080:8080 \
  --env-file .env \
  ym-processor
```

#### С Docker Compose
```bash
# Использование готовой конфигурации
cp config/docker-compose.yml .
docker-compose up -d
```

## 🖥️ Локальное развертывание

### 1. Установка зависимостей
```bash
# Python зависимости
pip install -r requirements.txt

# Для разработки
pip install -r requirements-dev.txt
```

### 2. Настройка окружения
```bash
export FAL_KEY="your_fal_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export LORA_PATH="https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors"
```

### 3. Запуск приложения
```bash
# Полное приложение
python app_batch.py

# Простое API
python app_api.py
```

## 🤖 Автоматическое развертывание

### Подготовка сервера
```bash
# На сервере установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER
```

### Настройка SSH доступа
```bash
# Сгенерируйте SSH ключ (если нет)
ssh-keygen -t rsa -b 4096

# Скопируйте ключ на сервер
ssh-copy-id root@your-server-ip
```

### Автоматическое развертывание
```bash
# Отредактируйте auto_deploy.sh с вашими настройками
nano auto_deploy.sh

# Обновите IP адрес и пароль
# Обновите API ключи

# Запустите развертывание
./auto_deploy.sh
```

## 🌐 Облачные платформы

### Render.com
1. Загрузите код в GitHub
2. Подключите репозиторий к Render
3. Используйте файл `render.yaml`
4. Добавьте переменные окружения в панели управления

### DigitalOcean App Platform
```yaml
name: ym-image-processor
services:
- name: web
  source_dir: /
  github:
    repo: your-username/ym-image-processor
    branch: main
  build_command: pip install -r requirements.txt
  run_command: python app_batch.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: FAL_KEY
    value: your_api_key
  - key: OPENAI_API_KEY  
    value: your_api_key
```

### AWS EC2 / Google Cloud
```bash
# Установка Docker на Ubuntu
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl enable docker

# Клонирование и запуск
git clone https://github.com/rslavai/ym-image-processor.git
cd ym-image-processor
# ... следуйте инструкциям Docker развертывания
```

## 🔧 Настройка и оптимизация

### Переменные окружения
```bash
# Основные
FAL_KEY=              # fal.ai API ключ (обязательно)
OPENAI_API_KEY=       # OpenAI API ключ (обязательно)
PORT=8080            # Порт приложения

# Дополнительные
LORA_PATH=           # Путь к LoRA модели
MAX_FILE_SIZE=10MB   # Максимальный размер файла
DEBUG=false          # Режим отладки
LOG_LEVEL=INFO       # Уровень логирования
```

### Производительность
```bash
# Для больших нагрузок
docker run -d \
  --name ym-processor \
  --restart always \
  -p 8080:8080 \
  --memory=4g \
  --cpus=2 \
  --env-file .env \
  ym-processor
```

### Мониторинг
```bash
# Просмотр логов
docker logs ym-processor -f

# Мониторинг ресурсов
docker stats ym-processor

# Проверка здоровья
curl http://localhost:8080/health
```

## 🔒 Безопасность

### Базовая защита
```bash
# Установка firewall
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8080  # Приложение
```

### SSL сертификат (Let's Encrypt)
```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавьте: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Ограничения доступа
```nginx
# В конфигурации nginx
location / {
    # Rate limiting
    limit_req zone=api burst=10 nodelay;
    
    # IP whitelist (опционально)
    allow 192.168.1.0/24;
    deny all;
    
    proxy_pass http://127.0.0.1:8080;
}
```

## 🧪 Тестирование развертывания

### Проверочный список
- [ ] Сервис отвечает на `/health`
- [ ] Загрузка изображения работает
- [ ] GPT-4 анализ выполняется  
- [ ] LoRA V1 обрабатывает изображения
- [ ] LoRA V2 обрабатывает изображения
- [ ] Fallback на BiRefNet работает
- [ ] База данных сохраняет результаты

### Автоматические тесты
```bash
# Запуск тестов
python -m pytest tests/ -v

# Тест конкретного компонента
python test_processor.py
```

### Нагрузочное тестирование
```bash
# Установка Apache Bench
sudo apt install apache2-utils

# Тест производительности
ab -n 100 -c 10 -T 'multipart/form-data' \
   -p test-image.jpg \
   http://localhost:8080/process_single
```

## 🆘 Устранение неполадок

### Частые проблемы

#### 1. Контейнер не запускается
```bash
# Проверка логов
docker logs ym-processor

# Возможные причины:
# - Неверные API ключи
# - Недостаточно памяти
# - Порт занят
```

#### 2. API ошибки
```bash
# Проверка API ключей
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Проверка fal.ai
curl -H "Authorization: Key $FAL_KEY" \
     https://fal.run/status
```

#### 3. Медленная обработка
```bash
# Увеличение ресурсов
docker update --memory=8g --cpus=4 ym-processor

# Мониторинг использования
docker stats ym-processor
```

#### 4. Ошибки базы данных
```bash
# Проверка базы данных
python scripts/check_database.py

# Восстановление базы
rm database/history.db
# База создастся автоматически при запуске
```

### Логи и диагностика
```bash
# Подробные логи
docker logs ym-processor --tail 100 -f

# Проверка внутри контейнера
docker exec -it ym-processor bash

# Проверка переменных окружения
docker exec ym-processor env | grep -E "(FAL|OPENAI)"
```

## 📞 Поддержка

### Документация
- [Техническое описание](TECHNICAL_OVERVIEW.md)
- [API документация](API_DOCUMENTATION.md)
- [История изменений](../CHANGELOG.md)

### Контакты
- **GitHub Issues**: Создайте issue в репозитории
- **Email**: Укажите контактный email
- **Документация**: См. папку `docs/`

---

**Руководство обновлено**: 8 января 2025  
**Версия**: 2.0  
**Совместимость**: Docker 20.10+, Python 3.9+