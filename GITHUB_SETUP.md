# 🔐 Настройка GitHub Secrets для автодеплоя

## 📋 Шаг 1: Добавление секретов в GitHub

1. Перейдите в настройки репозитория:
   ```
   https://github.com/rslavai/ym-image-processor/settings/secrets/actions
   ```

2. Нажмите **"New repository secret"** и добавьте следующие секреты:

### Секреты для подключения к серверу:

- **Name**: `SERVER_HOST`
  **Value**: `103.136.69.249`

- **Name**: `SERVER_PASSWORD` 
  **Value**: `wBlO#rH6yDy2z0oB0J`

### Секреты для webhook:

- **Name**: `WEBHOOK_SECRET`
  **Value**: `ym-deploy-secret-2024`

## 📋 Шаг 2: Настройка GitHub Webhook

1. Перейдите в настройки webhook:
   ```
   https://github.com/rslavai/ym-image-processor/settings/hooks
   ```

2. Нажмите **"Add webhook"**

3. Заполните поля:
   - **Payload URL**: `http://103.136.69.249:9000/webhook`
   - **Content type**: `application/json`
   - **Secret**: `ym-deploy-secret-2024`
   - **Which events would you like to trigger this webhook?**: 
     ☑️ Just the push event
   - **Active**: ☑️

4. Нажмите **"Add webhook"**

## 🚀 Как это работает

### Автоматический деплой через GitHub Actions:
1. Push в main ветку → GitHub Actions запускается
2. GitHub Actions подключается к серверу по SSH
3. Выполняется git pull и пересборка Docker контейнера
4. Приложение перезапускается

### Мгновенный деплой через Webhook:
1. Push в main ветку → GitHub отправляет webhook
2. Webhook сервер на порту 9000 получает уведомление
3. Запускается скрипт деплоя (git pull + docker rebuild)
4. Приложение обновляется за ~2 минуты

## 🔍 Мониторинг деплоя

### GitHub Actions логи:
```
https://github.com/rslavai/ym-image-processor/actions
```

### Webhook логи на сервере:
```bash
# Подключиться к серверу
ssh root@103.136.69.249

# Посмотреть логи webhook
journalctl -u ym-webhook -f

# Посмотреть логи деплоя
tail -f /var/log/webhook_deploy.log

# Проверить статус контейнера
docker ps | grep ym-processor
docker logs ym-processor --tail 20
```

## 🛠️ Тестирование

### Проверка webhook:
```bash
curl -X POST \
  http://103.136.69.249:9000/health \
  -H "Content-Type: application/json"
```

### Ручной деплой:
```bash
curl -X POST \
  http://103.136.69.249:9000/deploy \
  -H "X-Deploy-Secret: ym-deploy-secret-2024"
```

## 🔧 Решение проблем

### GitHub Actions не работает:
1. Проверьте правильность секретов
2. Убедитесь, что сервер доступен
3. Проверьте логи Actions

### Webhook не работает:
1. Проверьте URL в настройках webhook
2. Убедитесь, что порт 9000 открыт
3. Проверьте статус сервиса: `systemctl status ym-webhook`

### Приложение не запускается:
1. Проверьте логи Docker: `docker logs ym-processor`
2. Проверьте .env файл
3. Убедитесь, что все API ключи корректны