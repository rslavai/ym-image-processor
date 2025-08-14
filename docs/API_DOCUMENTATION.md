# 📡 API Документация

## 🌐 Базовая информация

**Base URL**: `http://103.136.69.249:8080`  
**Content Type**: `application/json` или `multipart/form-data`  
**Версия**: 2.0  

## 📋 Основные эндпоинты

### 🏠 Главная страница
```http
GET /
```
**Описание**: Отображает главную страницу с интерфейсом загрузки

**Ответ**: HTML страница с формой загрузки изображений

---

### 🖼️ Обработка одного изображения

#### Запуск обработки
```http
POST /process_single
```

**Параметры (multipart/form-data)**:
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `file` | File | Да | Изображение (PNG, JPEG, WEBP, max 10MB) |
| `enhance` | Boolean | Нет | Включить улучшенную обработку |
| `debug` | Boolean | Нет | Режим отладки |
| `modelId` | String | Нет | ID модели (если не указан - автовыбор) |
| `custom_prompt` | Boolean | Нет | Использовать пользовательский промпт |
| `custom_prompt_text` | String | Нет | Текст пользовательского промпта |

**Пример запроса**:
```bash
curl -X POST http://103.136.69.249:8080/process_single \
  -F "file=@image.jpg" \
  -F "modelId=flux-kontext-lora-v2" \
  -F "enhance=true"
```

**Ответ**:
```json
{
  "processing_id": "uuid-string"
}
```

#### Отслеживание прогресса
```http
GET /single_progress/<processing_id>
```

**Ответ**:
```json
{
  "status": "processing",
  "current_step": "background",
  "gpt_completed": true,
  "background_processing": true,
  "background_completed": false,
  "final_processing": false,
  "final_completed": false,
  "error": null,
  "original_image_url": "/single_image/{id}/original",
  "background_image_url": "/single_image/{id}/background",
  "final_image_url": "/single_image/{id}/final"
}
```

**Статусы**:
- `uploading` - Загрузка файла
- `analyzing` - GPT-4 анализ
- `background` - Удаление фона  
- `final` - Финальная обработка
- `completed` - Завершено
- `error` - Ошибка

#### Получение изображений
```http
GET /single_image/<processing_id>/<step>
```

**Параметры**:
- `step`: `original`, `background`, `final`

**Ответ**: Изображение в формате PNG

---

### 📦 Пакетная обработка

#### Запуск пакетной обработки
```http
POST /process_batch
```

**Параметры (multipart/form-data)**:
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `files` | File[] | Да | Множественные изображения |
| `lora_version` | String | Нет | Версия LoRA модели |
| `enhance` | Boolean | Нет | Включить улучшения |

**Ответ**:
```json
{
  "batch_id": "batch-uuid"
}
```

#### Прогресс пакетной обработки
```http
GET /batch_progress/<batch_id>
```

**Ответ**:
```json
{
  "batch_id": "batch-uuid",
  "total_files": 5,
  "processed_files": 2,
  "current_file": "image3.jpg",
  "status": "processing",
  "results": [
    {
      "filename": "image1.jpg",
      "status": "completed",
      "original_url": "/batch_image/{batch_id}/image1_original.png",
      "processed_url": "/batch_image/{batch_id}/image1_processed.png"
    }
  ]
}
```

#### Скачивание результатов
```http
GET /download_batch/<batch_id>
```

**Ответ**: ZIP архив с обработанными изображениями

---

### 🤖 Управление моделями

#### Список доступных моделей
```http
GET /models
```

**Описание**: Возвращает список всех доступных моделей для обработки изображений

**Ответ**:
```json
{
  "success": true,
  "models": [
    {
      "id": "flux-kontext-lora-v2",
      "name": "FLUX Kontext LoRA",
      "version": "v2",
      "provider": "fal-ai",
      "dataset_notes": "Улучшенная модель с расширенным датасетом",
      "pros": ["Высокое качество", "Точные края"],
      "cons": ["Медленнее V1", "Требовательна к ресурсам"],
      "spec": {
        "guidance_scale": 3.5,
        "num_inference_steps": 50,
        "memory_usage": "medium"
      }
    }
  ]
}
```

#### Информация о модели
```http
GET /models/:model_id
```

**Параметры**:
| Параметр | Описание |
|----------|----------|
| `model_id` | ID модели (например: flux-kontext-lora-v2) |

**Ответ**:
```json
{
  "success": true,
  "model": {
    "id": "flux-kontext-lora-v2",
    "name": "FLUX Kontext LoRA",
    "version": "v2",
    "provider": "fal-ai",
    "endpoint": "fal-ai/flux-kontext-lora",
    "dataset_notes": "Улучшенная модель, обученная на расширенном датасете",
    "pros": [
      "Высокое качество обработки",
      "Точное выделение краев",
      "Работает с прозрачными объектами"
    ],
    "cons": [
      "Медленнее V1 (50 сек)",
      "Выше требования к ресурсам"
    ],
    "spec": {
      "guidance_scale": 3.5,
      "num_inference_steps": 50,
      "supports_alpha": true,
      "max_resolution": "1024x1024",
      "memory_usage": "medium"
    },
    "tags": ["ecommerce", "background-removal", "enhanced"],
    "supports_marketplaces": ["yandex-market", "ozon", "wildberries"]
  }
}
```

---

### 📊 Сервисная информация

#### Проверка состояния
```http
GET /health
```

**Ответ**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T19:30:00Z",
  "services": {
    "openai": true,
    "fal_ai": true,
    "database": true
  }
}
```

#### История обработки
```http
GET /history
```

**Параметры**:
- `limit` (query): Количество записей (по умолчанию 50)
- `batch_id` (query): Фильтр по batch_id

**Ответ**:
```json
{
  "history": [
    {
      "id": 1,
      "batch_id": "batch-uuid",
      "filename": "image.jpg",
      "upload_time": "2025-01-08T19:30:00Z",
      "processing_time": 45.2,
      "status": "completed",
      "file_size": 2048576,
      "analysis": {
        "category": "electronics",
        "description": "Smartphone with blue case"
      }
    }
  ]
}
```

---

## 🎨 LoRA Модели

### LoRA V1 (Базовая)
- **Шаги**: 30
- **Guidance Scale**: 2.5
- **Время обработки**: 15-25 сек
- **Качество**: Хорошее для простых изображений

### LoRA V2 (Улучшенная)  
- **Шаги**: 50
- **Guidance Scale**: 3.5
- **Время обработки**: 25-40 сек
- **Качество**: Отличное для сложных изображений

### Fallback (BiRefNet)
- **Время обработки**: 5-10 сек
- **Качество**: Базовое
- **Использование**: Автоматически при сбоях LoRA

---

## 🧠 GPT-4 Анализ

### Входные данные
- Изображение товара (base64)
- Контекст: "Анализ товара для интернет-магазина"

### Выходные данные
```json
{
  "category": "electronics",
  "subcategory": "smartphones", 
  "brand": "Apple",
  "product_name": "iPhone 15 Pro",
  "description": "Современный смартфон с титановым корпусом",
  "colors": ["black", "titanium"],
  "materials": ["titanium", "glass"],
  "key_features": ["Face ID", "48MP camera", "Action Button"],
  "recommended_prompt": "Professional product photo of iPhone 15 Pro..."
}
```

---

## ❌ Коды ошибок

### HTTP статус коды
- `200` - Успешно
- `400` - Неверный запрос (неподдерживаемый формат файла)
- `404` - Не найдено (неверный processing_id)
- `413` - Файл слишком большой (>10MB)
- `500` - Внутренняя ошибка сервера

### Коды ошибок приложения
```json
{
  "error": "INVALID_FILE_FORMAT",
  "message": "Поддерживаются только PNG, JPEG, WEBP",
  "code": 4001
}
```

**Основные коды**:
- `4001` - Неподдерживаемый формат файла
- `4002` - Файл поврежден
- `4003` - Файл слишком большой
- `5001` - Ошибка API OpenAI
- `5002` - Ошибка API fal.ai
- `5003` - Ошибка базы данных

---

## 🔧 Примеры использования

### Python
```python
import requests

# Загрузка и обработка изображения
with open('product.jpg', 'rb') as f:
    response = requests.post(
        'http://103.136.69.249:8080/process_single',
        files={'file': f},
        data={
            'lora_version': 'v2',
            'enhance': 'true'
        }
    )

processing_id = response.json()['processing_id']

# Отслеживание прогресса
while True:
    progress = requests.get(f'http://103.136.69.249:8080/single_progress/{processing_id}')
    status = progress.json()
    
    if status['status'] == 'completed':
        # Скачивание результата
        result = requests.get(f'http://103.136.69.249:8080/single_image/{processing_id}/final')
        with open('result.png', 'wb') as f:
            f.write(result.content)
        break
    elif status['status'] == 'error':
        print(f"Ошибка: {status['error']}")
        break
    
    time.sleep(2)
```

### JavaScript
```javascript
// Загрузка файла
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('lora_version', 'v2');

fetch('/process_single', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    const processingId = data.processing_id;
    
    // Отслеживание прогресса
    const checkProgress = setInterval(() => {
        fetch(`/single_progress/${processingId}`)
        .then(response => response.json())
        .then(status => {
            if (status.status === 'completed') {
                clearInterval(checkProgress);
                document.getElementById('result').src = 
                    `/single_image/${processingId}/final`;
            } else if (status.status === 'error') {
                clearInterval(checkProgress);
                console.error(status.error);
            }
        });
    }, 2000);
});
```

### cURL
```bash
# Простая обработка
curl -X POST http://103.136.69.249:8080/process_single \
  -F "file=@product.jpg" \
  -F "modelId=flux-kontext-lora-v2"

# Проверка прогресса
curl http://103.136.69.249:8080/single_progress/{processing_id}

# Скачивание результата
curl -O http://103.136.69.249:8080/single_image/{processing_id}/final
```

---

## 🚀 Rate Limits

- **Одновременные запросы**: 10 на IP
- **Максимальный размер файла**: 10 MB
- **Таймаут обработки**: 120 секунд
- **История**: Хранится 30 дней

---

**Документация обновлена**: 8 января 2025  
**Версия API**: 2.0  
**Поддержка**: См. техническую документацию