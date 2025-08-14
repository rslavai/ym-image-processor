# 🚀 Инструкция по деплою YM Image Processor

## Быстрый деплой на сервер

### Вариант 1: Простой Docker (рекомендуется)

1. **Скопируйте на сервер файл `deploy_server.sh`:**
```bash
scp deploy_server.sh root@103.136.69.249:/opt/deploy_ym.sh
```

2. **Подключитесь к серверу и запустите скрипт:**
```bash
ssh root@103.136.69.249
chmod +x /opt/deploy_ym.sh
/opt/deploy_ym.sh
```

### Вариант 2: Docker Compose (продвинутый)

1. **На сервере клонируйте репозиторий:**
```bash
cd /opt
git clone https://github.com/rslavai/ym-image-processor.git
cd ym-image-processor
```

2. **Создайте файл `.env`:**
```bash
cat > .env << 'EOF'
FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5
LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors
OPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw
PORT=8080
EOF
```

3. **Запустите через docker-compose:**
```bash
docker-compose up -d
```

### Вариант 3: Ручной деплой

Если автоматические скрипты не работают:

```bash
# 1. Подключитесь к серверу
ssh root@103.136.69.249

# 2. Перейдите в директорию проекта
cd /opt/ym-image-processor

# 3. Обновите код
git pull origin main

# 4. Создайте .env файл (если его нет)
cat > .env << 'EOF'
FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5
LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors
OPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw
PORT=8080
EOF

# 5. Пересоберите Docker образ
docker build -t ym-processor .

# 6. Остановите старый контейнер
docker stop ym-processor
docker rm ym-processor

# 7. Запустите новый контейнер
docker run -d \
  --name ym-processor \
  --restart always \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/database:/app/database \
  -v $(pwd)/processed:/app/processed \
  -v $(pwd)/uploads:/app/uploads \
  ym-processor

# 8. Проверьте логи
docker logs ym-processor

# 9. Проверьте статус
curl http://localhost:8080/health
```

## 📊 Проверка работы системы

После деплоя проверьте:

1. **Health endpoint:**
```bash
curl http://103.136.69.249/health
```

Должен вернуть:
```json
{
  "service": "ym-batch-processor",
  "status": "healthy",
  "openai_configured": true,
  "fal_configured": true
}
```

2. **Откройте в браузере:**
http://103.136.69.249

## 🛠 Управление системой

### Просмотр логов
```bash
docker logs -f ym-processor
```

### Перезапуск
```bash
docker restart ym-processor
```

### Остановка
```bash
docker stop ym-processor
```

### Обновление
```bash
cd /opt/ym-image-processor
git pull
docker-compose down
docker-compose up -d --build
```

## 📈 Мониторинг

### Просмотр метрик
```bash
docker exec ym-processor cat /app/logs/processing_summary.json
```

### Просмотр ошибок
```bash
docker exec ym-processor tail -f /app/logs/errors.jsonl
```

### Использование ресурсов
```bash
docker stats ym-processor
```

## 🔧 Решение проблем

### Если контейнер не запускается
1. Проверьте логи: `docker logs ym-processor`
2. Проверьте .env файл
3. Убедитесь, что порт 8080 свободен: `netstat -tlnp | grep 8080`

### Если нет доступа извне
1. Проверьте firewall: `ufw status`
2. Откройте порт: `ufw allow 8080/tcp`
3. Проверьте, что Docker слушает на всех интерфейсах

### Если GPT-4 Vision не работает
1. Проверьте API ключ в .env
2. Проверьте логи на ошибки API
3. Убедитесь, что ключ активен

## 📝 Что делает система

После успешного деплоя вы получите:

1. **Batch Processing** - обработка до 100 изображений одновременно
2. **GPT-4 Vision Analysis** - умный анализ каждого товара
3. **Smart Positioning** - автоматическое размещение на canvas
4. **Background Removal** - удаление фона через LoRA
5. **Processing History** - сохранение истории в SQLite
6. **ZIP Export** - скачивание результатов архивом

## 🎯 Использование

1. Откройте http://103.136.69.249
2. Загрузите изображения товаров (до 100 штук)
3. Система автоматически:
   - Проанализирует каждое изображение через GPT-4 Vision
   - Определит категорию и свойства товара
   - Удалит фон через вашу LoRA модель
   - Разместит на правильном canvas (1:1 или 3:4)
   - Выровняет согласно типу товара
4. Скачайте результаты в ZIP архиве

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker logs ym-processor`
2. Проверьте статус: `docker ps`
3. Перезапустите: `docker restart ym-processor`