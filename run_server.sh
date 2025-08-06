#!/bin/bash

# Скрипт для безопасного запуска Flask сервера
# Автоматически освобождает порт и запускает сервер

PORT=8080
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "="
echo "🚀 Запуск сервиса обработки изображений"
echo "="

# Проверяем, занят ли порт
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Порт $PORT занят. Освобождаем..."
    # Находим и останавливаем процесс
    PID=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
    kill $PID 2>/dev/null
    sleep 1
    echo "✅ Порт освобожден"
fi

# Переходим в директорию проекта
cd "$SCRIPT_DIR"

# Проверяем наличие зависимостей
echo "📦 Проверка зависимостей..."
python3 -c "import rembg" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Устанавливаем недостающие зависимости..."
    pip3 install rembg onnxruntime pillow flask
fi

# Запускаем сервер
echo "🔧 Запуск сервера на порту $PORT..."
echo ""
echo "📱 Откройте в браузере:"
echo "   👉 http://localhost:$PORT"
echo "   👉 http://127.0.0.1:$PORT"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo "="
echo ""

# Запускаем Flask приложение
python3 simple_flask_ui.py