# 🚀 Настройка автоматического деплоя

После выполнения этой инструкции ваш сервер будет автоматически обновляться при каждом push в GitHub!

## 📋 Быстрая установка (5 минут)

### Шаг 1: Подключитесь к серверу
```bash
ssh root@103.136.69.249
```

### Шаг 2: Скачайте и запустите скрипт установки
```bash
# Скачать скрипт
curl -o /tmp/setup_autodeploy.sh https://raw.githubusercontent.com/rslavai/ym-image-processor/main/setup_autodeploy.sh

# Сделать исполняемым
chmod +x /tmp/setup_autodeploy.sh

# Запустить установку
/tmp/setup_autodeploy.sh
```

Скрипт автоматически:
- ✅ Установит webhook сервер
- ✅ Создаст systemd service
- ✅ Настроит автозапуск
- ✅ Откроет порт 9000

### Шаг 3: Настройте GitHub Webhook

1. Откройте настройки репозитория:
   https://github.com/rslavai/ym-image-processor/settings/hooks

2. Нажмите **"Add webhook"**

3. Заполните поля:
   - **Payload URL**: `http://103.136.69.249:9000/webhook`
   - **Content type**: `application/json`
   - **Secret**: `ym-deploy-secret-2024`
   - **Which events?**: `Just the push event`
   - **Active**: ✅

4. Нажмите **"Add webhook"**

### Шаг 4: Проверьте работу

GitHub автоматически отправит ping на ваш webhook. Проверьте статус:

```bash
# На сервере проверьте логи
journalctl -u webhook -n 20
```

Вы должны увидеть: `Webhook ping successful`

## 🎯 Тестирование автодеплоя

1. Сделайте небольшое изменение в коде:
```bash
# На локальной машине
cd "/Users/shorstov/Desktop/AI/K+ content service"
echo "# Test autodeploy $(date)" >> README.md
git add README.md
git commit -m "Test autodeploy"
git push origin main
```

2. Проверьте на сервере (деплой займет 1-2 минуты):
```bash
# Смотрите логи webhook
journalctl -u webhook -f

# Смотрите логи деплоя
tail -f /var/log/webhook_deploy.log

# Проверьте статус контейнера
docker ps | grep ym-processor
```

## 📊 Мониторинг автодеплоя

### Просмотр логов webhook сервера
```bash
journalctl -u webhook -f
```

### Просмотр логов деплоя
```bash
tail -f /var/log/webhook_deploy.log
```

### Проверка статуса службы
```bash
systemctl status webhook
```

### История деплоев
```bash
grep "Deployment completed" /var/log/webhook_deploy.log
```

## 🛠 Управление автодеплоем

### Остановить автодеплой
```bash
systemctl stop webhook
```

### Запустить автодеплой
```bash
systemctl start webhook
```

### Перезапустить webhook сервер
```bash
systemctl restart webhook
```

### Ручной деплой (если нужно)
```bash
curl -X POST \
  -H "X-Deploy-Secret: ym-deploy-secret-2024" \
  http://localhost:9000/deploy
```

## 🔒 Безопасность

### Изменить секретный ключ webhook

1. На сервере:
```bash
# Отредактируйте service файл
nano /etc/systemd/system/webhook.service

# Измените строку:
Environment="WEBHOOK_SECRET=ваш-новый-секрет"

# Перезапустите
systemctl daemon-reload
systemctl restart webhook
```

2. В GitHub webhook настройках обновите Secret на новый

### Ограничить доступ к webhook

Добавьте в nginx только разрешенные IP GitHub:
```nginx
location /webhook {
    # Разрешить только GitHub IPs
    allow 140.82.112.0/20;
    allow 143.55.64.0/20;
    allow 185.199.108.0/22;
    allow 192.30.252.0/22;
    deny all;
    
    proxy_pass http://localhost:9000/webhook;
}
```

## 🚨 Решение проблем

### Webhook не работает

1. Проверьте, что порт 9000 открыт:
```bash
netstat -tlnp | grep 9000
ufw allow 9000/tcp
```

2. Проверьте логи:
```bash
journalctl -u webhook -n 50
```

3. Тест webhook вручную:
```bash
curl http://localhost:9000/health
```

### Деплой не происходит

1. Проверьте права на deploy скрипт:
```bash
ls -la /opt/deploy_ym.sh
chmod +x /opt/deploy_ym.sh
```

2. Запустите деплой вручную:
```bash
/opt/deploy_ym.sh
```

3. Проверьте Docker:
```bash
docker ps -a
docker logs ym-processor
```

### GitHub показывает ошибку

1. Проверьте Secret в настройках webhook
2. Проверьте URL (должен быть http, не https)
3. Попробуйте Redeliver failed webhook в GitHub

## 📈 Дополнительные возможности

### Уведомления в Telegram

Добавьте в webhook_server.py:
```python
def send_telegram_notification(message):
    bot_token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})

# В функции run_deployment():
send_telegram_notification(f"✅ Deployment completed for YM Image Processor")
```

### Откат при ошибке

Добавьте в deploy_ym.sh:
```bash
# Сохранить текущий образ перед обновлением
docker tag ym-processor ym-processor:backup

# Если деплой failed, откатиться
if [ $? -ne 0 ]; then
    docker stop ym-processor
    docker rm ym-processor
    docker tag ym-processor:backup ym-processor
    docker run -d --name ym-processor ... ym-processor
fi
```

## ✅ Готово!

Теперь ваш сервер будет автоматически обновляться при каждом push в main ветку GitHub!

Процесс деплоя:
1. Вы делаете `git push` → 
2. GitHub отправляет webhook → 
3. Сервер получает уведомление → 
4. Запускается deploy_ym.sh → 
5. Обновляется Docker контейнер → 
6. Новая версия работает!

Весь процесс занимает 1-2 минуты.