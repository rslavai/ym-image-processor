# 🚀 Начало работы с Yandex Market Image Processor

## 📋 Содержание

1. [Требования](#требования)
2. [Установка](#установка)
3. [Первый запуск](#первый-запуск)
4. [Базовое использование](#базовое-использование)
5. [Структура данных](#структура-данных)
6. [Часто задаваемые вопросы](#часто-задаваемые-вопросы)

## 📦 Требования

### Системные требования

- **ОС**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8 или выше
- **RAM**: минимум 8 GB (рекомендуется 16 GB для пакетной обработки)
- **GPU**: опционально, но значительно ускоряет обработку

### Проверка Python

```bash
python --version
# или
python3 --version
```

Должно вывести версию Python 3.8 или выше.

## 🛠️ Установка

### 1. Клонирование репозитория

```bash
git clone [URL репозитория]
cd yandex-market-image-processor
```

### 2. Создание виртуального окружения

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

**Базовая установка:**
```bash
pip install -r requirements.txt
```

**Полная установка (с инструментами разработки):**
```bash
pip install -r requirements-dev.txt
```

### 4. Проверка установки

```bash
python -c "import cv2, PIL, rembg; print('Все библиотеки установлены!')"
```

## 🎯 Первый запуск

### Простой пример

1. Поместите тестовое изображение в папку `data/input/`

2. Создайте файл `test.py`:

```python
from src.processors.background import BackgroundRemover

# Создаем обработчик
remover = BackgroundRemover()

# Удаляем фон
result = remover.process("data/input/test_image.jpg")

# Сохраняем результат
result.save("data/output/test_result.png")
print("Готово! Проверьте data/output/test_result.png")
```

3. Запустите:
```bash
python test.py
```

## 💻 Базовое использование

### Обработка одного изображения

```python
from src.main import ImageProcessor

processor = ImageProcessor()

# Обработка с указанием категории
result = processor.process_single(
    image_path="path/to/image.jpg",
    category="fashion",  # fashion, beauty, home, cehac
    output_dir="data/output"
)
```

### Пакетная обработка

```python
# Обработка всех изображений в папке
results = processor.process_batch(
    input_dir="data/input/fashion",
    category="fashion",
    output_dir="data/output/fashion"
)

print(f"Обработано {len(results)} изображений")
```

### Настройка параметров

```python
# Создание процессора с кастомными настройками
processor = ImageProcessor(
    light_bg_color="#F5F4F2",  # Цвет светлого фона
    dark_bg_color="#D1CECB",   # Цвет темного фона
    target_size=(1600, 1600),  # Целевой размер
    shadow_opacity=0.3,        # Прозрачность тени
    upscale_model="realesrgan" # Модель для увеличения
)
```

## 📁 Структура данных

### Входные данные

Разместите изображения в соответствующих папках:

```
data/input/
├── fashion/      # Одежда, обувь
├── beauty/       # Косметика
├── home/         # Товары для дома
└── cehac/        # Электроника
```

### Выходные данные

Обработанные изображения сохраняются в:

```
data/output/
├── product_sku_light.jpg   # Светлая версия
└── product_sku_dark.jpg    # Темная версия
```

## ❓ Часто задаваемые вопросы

### Какие форматы изображений поддерживаются?

- **Входные**: JPEG, PNG, BMP, TIFF
- **Выходные**: JPEG (для финальных), PNG (для промежуточных с прозрачностью)

### Как ускорить обработку?

1. Используйте GPU версию библиотек
2. Обрабатывайте изображения пакетами
3. Уменьшите размер входных изображений, если они очень большие

### Что делать, если фон удаляется неправильно?

1. Убедитесь, что объект хорошо контрастирует с фоном
2. Попробуйте предварительно обрезать лишнее пространство
3. Используйте изображения с более высоким разрешением

### Как добавить свои правила для категории?

См. документацию по [созданию категорий](development/custom_categories.md).

## 🔧 Решение проблем

### Ошибка импорта модулей

```bash
# Переустановите зависимости
pip install --upgrade -r requirements.txt
```

### Недостаточно памяти

- Уменьшите размер пакета при batch обработке
- Закройте другие приложения
- Используйте параметр `low_memory_mode=True`

### Медленная работа

- Установите GPU версии библиотек
- Используйте меньший размер изображений для тестов
- Включите многопоточность: `processor.set_workers(4)`

## 📚 Дополнительные ресурсы

- [Архитектура проекта](architecture.md)
- [API документация](api/index.md)
- [Примеры использования](../examples/)
- [Вклад в проект](../CONTRIBUTING.md)

---

Нужна помощь? Создайте issue в репозитории или свяжитесь с командой разработки.