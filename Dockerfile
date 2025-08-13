FROM python:3.9-slim

# Установка системных зависимостей для OpenCV и обработки изображений
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание директории для загрузок и базы данных
RUN mkdir -p /app/uploads /app/processed /app/database

# Открытие порта
EXPOSE 8080

# Запуск batch версии с полным функционалом
CMD ["python3", "app_batch.py"]