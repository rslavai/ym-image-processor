# 🚀 Деплой на внешний сервер

## Варианты деплоя

### 1. Render.com (Рекомендуется - БЕСПЛАТНО)

1. **Создайте аккаунт на [Render.com](https://render.com)**

2. **Загрузите код на GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ym-image-processor.git
   git push -u origin main
   ```

3. **Подключите репозиторий к Render:**
   - Зайдите в Dashboard Render
   - Нажмите "New +" → "Web Service"
   - Подключите GitHub аккаунт
   - Выберите ваш репозиторий
   - Настройки:
     - Name: `ym-image-processor`
     - Environment: `Docker`
     - Branch: `main`
     - Auto-Deploy: `Yes`

4. **Дождитесь деплоя** (около 10 минут первый раз)

5. **Ваш сервис будет доступен по адресу:**
   ```
   https://ym-image-processor.onrender.com
   ```

### 2. Railway.app (Альтернатива - $5 кредит)

1. **Создайте аккаунт на [Railway.app](https://railway.app)**

2. **Деплой через GitHub:**
   ```bash
   # Установите Railway CLI
   npm install -g @railway/cli
   
   # Логин
   railway login
   
   # Создайте проект
   railway init
   
   # Деплой
   railway up
   ```

3. **Получите URL вашего сервиса:**
   ```bash
   railway open
   ```

### 3. Heroku (Платный - от $5/месяц)

1. **Создайте файл `Procfile`:**
   ```
   web: gunicorn app:app --bind 0.0.0.0:$PORT
   ```

2. **Деплой:**
   ```bash
   heroku create ym-image-processor
   heroku stack:set container
   git push heroku main
   ```

### 4. Google Cloud Run (Есть бесплатный лимит)

1. **Установите gcloud CLI**

2. **Деплой:**
   ```bash
   gcloud run deploy ym-image-processor \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## 🔧 Локальное тестирование Docker

```bash
# Сборка образа
docker build -t ym-processor .

# Запуск контейнера
docker run -p 8080:8080 ym-processor

# Откройте http://localhost:8080
```

## 📊 Мониторинг

После деплоя вы можете проверить статус:
- Health check: `https://your-app.onrender.com/health`
- Главная страница: `https://your-app.onrender.com/`

## 🔄 Обновления

При push в main ветку GitHub, сервис автоматически обновится (если включен auto-deploy).

## ⚠️ Важные моменты

1. **Бесплатный план Render:**
   - Сервис засыпает после 15 минут неактивности
   - Первый запрос может занять 30-60 секунд
   - 750 часов в месяц бесплатно

2. **Оптимизация:**
   - Модель rembg загружается при первом запуске
   - Кеширование результатов включено
   - Максимальный размер файла: 16MB

3. **Масштабирование:**
   - Для production используйте платный план
   - Добавьте CDN для статики
   - Используйте S3 для хранения изображений

## 🆘 Поддержка

Если возникли проблемы:
1. Проверьте логи в Dashboard
2. Убедитесь что все зависимости в requirements.txt
3. Проверьте Dockerfile на ошибки