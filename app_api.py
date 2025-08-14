"""
YM Image Processor - версия с внешним API (Fal.ai)
Оптимизирована для Free хостинга - не требует памяти для моделей
"""
import os
import io
import base64
import requests
from flask import Flask, render_template_string, request, jsonify, send_file
from PIL import Image
import time
from src.models.model_registry import ModelRegistry

app = Flask(__name__)
model_registry = ModelRegistry()
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# API ключ из переменной окружения
# Support both FAL_KEY (official) and FAL_API_KEY (legacy)
FAL_API_KEY = os.environ.get('FAL_KEY') or os.environ.get('FAL_API_KEY', '')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>YM Image Processor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Syne', -apple-system, BlinkMacSystemFont, SF Pro Display, sans-serif;
            background: #ffffff;
            min-height: 100vh;
            padding: 60px 20px;
            position: relative;
        }
        
        /* Subtle background pattern */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                radial-gradient(circle at 20% 50%, rgba(120, 120, 120, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(120, 120, 120, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 40% 20%, rgba(120, 120, 120, 0.02) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        
        .container { 
            max-width: 920px; 
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        
        /* Glassmorphism card */
        .glass-card {
            background: rgba(248, 248, 248, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.5);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.08),
                inset 0 2px 1px rgba(255, 255, 255, 0.6);
            padding: 48px;
            position: relative;
            overflow: hidden;
        }
        
        /* Glass shimmer effect */
        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.2),
                transparent
            );
            transition: left 0.5s;
        }
        
        .glass-card:hover::before {
            left: 100%;
        }
        
        h1 { 
            font-size: 2.5rem;
            font-weight: 600;
            color: #1d1d1f;
            text-align: center;
            margin-bottom: 48px;
            letter-spacing: -0.02em;
        }
        
        .upload-zone {
            background: rgba(255, 255, 255, 0.5);
            border: 2px dashed rgba(0, 0, 0, 0.1);
            border-radius: 16px;
            padding: 60px 40px;
            text-align: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }
        
        .upload-zone:hover {
            background: rgba(255, 255, 255, 0.8);
            border-color: rgba(0, 0, 0, 0.2);
            transform: translateY(-2px);
        }
        
        .upload-zone.dragover {
            background: rgba(255, 255, 255, 0.9);
            border-color: #1d1d1f;
            transform: scale(1.02);
        }
        
        .file-input-wrapper {
            position: relative;
            overflow: hidden;
            display: inline-block;
        }
        
        .file-input-wrapper input[type=file] {
            position: absolute;
            left: -9999px;
        }
        
        .file-input-label {
            display: inline-block;
            padding: 0;
            background: none;
            color: #1d1d1f;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: opacity 0.3s;
        }
        
        .file-input-label:hover {
            opacity: 0.7;
        }
        
        .upload-icon {
            width: 48px;
            height: 48px;
            margin: 0 auto 20px;
            opacity: 0.3;
        }
        
        .upload-text {
            color: #86868b;
            font-size: 0.95rem;
            margin-top: 12px;
        }
        
        button { 
            background: #1d1d1f;
            color: #ffffff;
            padding: 14px 36px;
            border: none;
            cursor: pointer;
            border-radius: 100px;
            font-size: 1rem;
            font-weight: 500;
            margin-top: 32px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: -0.01em;
        }
        
        button:hover { 
            background: #000000;
            transform: scale(1.05);
        }
        
        button:active {
            transform: scale(0.98);
        }
        
        button:disabled {
            opacity: 0.3;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            margin: 48px 0;
        }
        
        .loading.active {
            display: block;
        }
        
        /* Linear progress bar instead of spinner */
        .progress-bar {
            width: 200px;
            height: 2px;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 2px;
            margin: 0 auto;
            overflow: hidden;
            position: relative;
        }
        
        .progress-bar::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: #1d1d1f;
            animation: progress 1.5s ease-in-out infinite;
        }
        
        @keyframes progress {
            0% { left: -100%; }
            50% { left: 100%; }
            100% { left: 100%; }
        }
        
        .loading-text {
            color: #86868b;
            font-size: 0.9rem;
            margin-top: 20px;
            text-align: center;
        }
        
        .result-area {
            display: none;
            margin-top: 60px;
        }
        
        .result-area.active {
            display: block;
            animation: fadeIn 0.5s ease-in-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .images-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            margin-top: 40px;
        }
        
        @media (max-width: 768px) {
            .images-grid {
                grid-template-columns: 1fr;
            }
            
            .glass-card {
                padding: 32px 24px;
            }
            
            h1 {
                font-size: 2rem;
            }
        }
        
        .image-box {
            text-align: center;
        }
        
        .image-box img {
            max-width: 100%;
            max-height: 400px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            background: white;
            padding: 8px;
        }
        
        .image-label {
            font-size: 0.85rem;
            color: #86868b;
            margin-bottom: 16px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .download-btn {
            background: #1d1d1f;
            color: white;
            display: inline-block;
            margin-top: 20px;
            padding: 12px 28px;
            text-decoration: none;
            border-radius: 100px;
            font-weight: 500;
            font-size: 0.95rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .download-btn:hover {
            background: #000000;
            transform: scale(1.05);
        }
        
        .status {
            padding: 16px 24px;
            margin: 32px 0;
            border-radius: 12px;
            font-weight: 500;
            text-align: center;
            font-size: 0.95rem;
            backdrop-filter: blur(10px);
        }
        
        .success {
            background: rgba(52, 199, 89, 0.1);
            color: #00733B;
            border: 1px solid rgba(52, 199, 89, 0.2);
        }
        
        .error {
            background: rgba(255, 59, 48, 0.1);
            color: #D70015;
            border: 1px solid rgba(255, 59, 48, 0.2);
        }
        
        .warning {
            background: rgba(255, 204, 0, 0.1);
            color: #A68B00;
            border: 1px solid rgba(255, 204, 0, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="glass-card">
            <h1>YM Image Processor</h1>
            
            {% if not api_configured %}
            <div class="status warning">
                API ключ не настроен. Добавьте FAL_API_KEY в переменные окружения.
            </div>
            {% endif %}
            
            <form method="POST" enctype="multipart/form-data" id="uploadForm">
                <div class="upload-zone" id="uploadZone">
                    <svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <div class="file-input-wrapper">
                        <input type="file" name="file" id="file" accept="image/*" required>
                        <label for="file" class="file-input-label">Выберите изображение</label>
                    </div>
                    <p class="upload-text">или перетащите файл сюда</p>
                </div>
                <button type="submit" id="processBtn">Обработать</button>
            </form>
            
            <div class="loading" id="loading">
                <div class="progress-bar"></div>
                <p class="loading-text">Обработка изображения...</p>
            </div>
            
            {% if status %}
            <div class="status {{ status_class }}">{{ status }}</div>
            {% endif %}
            
            <div class="result-area {% if output_image %}active{% endif %}">
                <div class="images-grid">
                    <div class="image-box">
                        <p class="image-label">Оригинал</p>
                        {% if input_image %}
                        <img src="data:image/png;base64,{{ input_image }}" alt="Original">
                        {% endif %}
                    </div>
                    <div class="image-box">
                        <p class="image-label">Результат</p>
                        {% if output_image %}
                        <img src="data:image/png;base64,{{ output_image }}" alt="Result">
                        <a href="data:image/png;base64,{{ output_image }}" download="result.png" class="download-btn">
                            Скачать PNG
                        </a>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('uploadForm').addEventListener('submit', function() {
            document.getElementById('loading').classList.add('active');
            document.getElementById('processBtn').disabled = true;
        });
        
        document.getElementById('file').addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                document.querySelector('.file-input-label').textContent = fileName;
            }
        });
        
        // Drag and drop
        const uploadZone = document.getElementById('uploadZone');
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
        });
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('file').files = files;
                document.querySelector('.file-input-label').textContent = files[0].name;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Главная страница."""
    api_configured = bool(FAL_API_KEY)
    return render_template_string(HTML_TEMPLATE, api_configured=api_configured)

@app.route('/', methods=['POST'])
def process():
    """Обработка изображения через Fal.ai API."""
    try:
        # Проверяем наличие файла
        if 'file' not in request.files:
            return render_template_string(HTML_TEMPLATE, 
                                         status='Файл не выбран',
                                         status_class='error')
        
        file = request.files['file']
        if file.filename == '':
            return render_template_string(HTML_TEMPLATE,
                                         status='Файл не выбран',
                                         status_class='error')
        
        # Читаем изображение
        input_image = Image.open(file.stream).convert('RGBA')
        
        # Сохраняем исходное для отображения
        input_buffer = io.BytesIO()
        input_image.save(input_buffer, format='PNG')
        input_base64 = base64.b64encode(input_buffer.getvalue()).decode()
        
        # Если нет API ключа, используем заглушку
        if not FAL_API_KEY:
            # Просто возвращаем исходное изображение с сообщением
            return render_template_string(HTML_TEMPLATE,
                                         input_image=input_base64,
                                         output_image=input_base64,
                                         status='API ключ не настроен. Показан оригинал.',
                                         status_class='warning',
                                         api_configured=False)
        
        # Вызов Fal.ai API для удаления фона
        result_image = remove_background_fal(input_image)
        
        if result_image:
            # Конвертируем результат в base64
            output_buffer = io.BytesIO()
            result_image.save(output_buffer, format='PNG')
            output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return render_template_string(HTML_TEMPLATE,
                                         input_image=input_base64,
                                         output_image=output_base64,
                                         status='Фон успешно удален',
                                         status_class='success',
                                         api_configured=True)
        else:
            return render_template_string(HTML_TEMPLATE,
                                         input_image=input_base64,
                                         status='Ошибка при обработке через API',
                                         status_class='error',
                                         api_configured=True)
        
    except Exception as e:
        return render_template_string(HTML_TEMPLATE,
                                     status=f'Ошибка: {str(e)}',
                                     status_class='error')

def remove_background_fal(image):
    """
    Удаление фона через вашу натренированную LoRA модель на Fal.ai
    Используем FLUX Kontext для умного редактирования с правильным fal_client
    """
    try:
        import fal_client
        print("✅ fal_client импортирован успешно")
        
        # Проверяем переменные окружения
        if not os.environ.get('FAL_KEY') and not os.environ.get('FAL_API_KEY'):
            print("❌ Ни FAL_KEY, ни FAL_API_KEY не настроены в переменных окружения")
            return None
        
        # Конвертируем изображение в base64 для отправки
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Получаем путь к вашей LoRA модели из переменных окружения
        lora_path = os.environ.get('LORA_PATH', 
            'https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors')
        
        # Настройка для отладки прогресса
        def on_queue_update(update):
            if isinstance(update, fal_client.InProgress):
                print(f"Processing: {len(update.logs)} logs received")
                for log in update.logs:
                    print(f"  {log.get('message', '')}")
        
        # Используем FLUX Kontext с вашей LoRA моделью через официальный клиент
        arguments = {
            "image_url": f"data:image/png;base64,{img_base64}",
            "prompt": "remove background, place product on pure white background, keep shadows for realism, professional product photography",
            "num_inference_steps": 30,
            "guidance_scale": 2.5,
            "output_format": "png",
            "enable_safety_checker": False,
            "loras": [
                {
                    "path": lora_path,
                    "scale": 1.0
                }
            ],
            "resolution_mode": "match_input"
        }
        
        # Отправляем запрос с подпиской на обновления
        print("🔄 Отправляем запрос к FLUX Kontext LoRA...")
        result = fal_client.subscribe(
            "fal-ai/flux-kontext-lora",
            arguments=arguments,
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        
        # Обрабатываем результат
        print(f"📋 Результат API: {type(result)}")
        if result:
            print(f"📋 Ключи в результате: {list(result.keys()) if isinstance(result, dict) else 'не dict'}")
        
        if result and 'images' in result and len(result['images']) > 0:
            img_url = result['images'][0]['url']
            # Загружаем результат
            img_response = requests.get(img_url)
            result_image = Image.open(io.BytesIO(img_response.content))
            print("✅ Успешно обработано с FLUX Kontext LoRA")
            return result_image
        
        print("❌ FLUX Kontext LoRA не вернул изображения")
        
        # Fallback на обычное удаление фона если LoRA не сработала
        print("🔄 Пробуем fallback на BiRefNet...")
        
        fallback_result = fal_client.subscribe(
            "fal-ai/birefnet",
            arguments={
                "image_url": f"data:image/png;base64,{img_base64}"
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        
        if fallback_result and 'image' in fallback_result:
            img_response = requests.get(fallback_result['image']['url'])
            result_image = Image.open(io.BytesIO(img_response.content))
            print("✅ Успешно обработано с BiRefNet fallback")
            return result_image
        
        print("❌ И BiRefNet fallback не сработал")
        return None
        
    except ImportError:
        print("❌ fal_client не установлен. Устанавливаем...")
        return None
    except Exception as e:
        print(f"❌ Ошибка при вызове Fal.ai API: {e}")
        return None

@app.route('/health')
def health():
    """Проверка состояния сервиса."""
    return jsonify({
        'status': 'healthy',
        'api_configured': bool(FAL_API_KEY),
        'service': 'ym-image-processor-api'
    })

@app.route('/models', methods=['GET'])
def get_models():
    """Получить список всех моделей."""
    try:
        models = model_registry.get_all_models(active_only=True)
        return jsonify({
            'success': True,
            'models': [model.to_dict() for model in models]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/models/<model_id>', methods=['GET'])
def get_model(model_id):
    """Получить детальную информацию о модели."""
    try:
        model = model_registry.get_model_by_id(model_id)
        if model:
            return jsonify({
                'success': True,
                'model': model.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Model {model_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting API-based server on port {port}")
    print(f"Fal.ai API configured: {bool(FAL_API_KEY)}")
    app.run(host='0.0.0.0', port=port, debug=False)