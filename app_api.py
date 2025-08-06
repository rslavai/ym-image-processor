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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# API ключ из переменной окружения
FAL_API_KEY = os.environ.get('FAL_API_KEY', '')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>YM Image Processor - API Version</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 { 
            font-size: 2em;
            margin-bottom: 10px;
        }
        .subtitle {
            opacity: 0.9;
            font-size: 1.1em;
        }
        .api-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            margin-top: 10px;
            font-size: 0.9em;
        }
        .content {
            padding: 30px;
        }
        .upload-area {
            border: 3px dashed #e0e0e0;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            background: #f8f9fa;
            transition: all 0.3s;
        }
        .upload-area:hover {
            border-color: #667eea;
            background: #f0f4ff;
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
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 30px;
            cursor: pointer;
            transition: transform 0.3s;
            font-weight: 600;
        }
        .file-input-label:hover {
            transform: translateY(-2px);
        }
        button { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            cursor: pointer;
            border-radius: 30px;
            font-size: 1.1em;
            font-weight: 600;
            margin-top: 20px;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .loading {
            display: none;
            margin: 30px 0;
        }
        .loading.active {
            display: block;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .result-area {
            display: none;
            margin-top: 40px;
        }
        .result-area.active {
            display: block;
        }
        .images-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 30px;
        }
        @media (max-width: 768px) {
            .images-grid {
                grid-template-columns: 1fr;
            }
        }
        .image-box {
            text-align: center;
        }
        .image-box img {
            max-width: 100%;
            max-height: 400px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .download-btn {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
            display: inline-block;
            margin-top: 15px;
            padding: 12px 30px;
            color: white;
            text-decoration: none;
            border-radius: 30px;
            font-weight: 600;
        }
        .status {
            padding: 15px;
            margin: 20px 0;
            border-radius: 10px;
            font-weight: 500;
            text-align: center;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        h4 {
            margin-bottom: 15px;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛍️ YM Image Processor</h1>
            <div class="subtitle">Профессиональное удаление фона для Яндекс Маркет</div>
            <div class="api-badge">⚡ Powered by Fal.ai</div>
        </div>
        
        <div class="content">
            {% if not api_configured %}
            <div class="status warning">
                ⚠️ API ключ не настроен. Добавьте FAL_API_KEY в переменные окружения Render.
            </div>
            {% endif %}
            
            <form method="POST" enctype="multipart/form-data" id="uploadForm">
                <div class="upload-area">
                    <p style="font-size: 3em; margin-bottom: 20px;">📸</p>
                    <div class="file-input-wrapper">
                        <input type="file" name="file" id="file" accept="image/*" required>
                        <label for="file" class="file-input-label">Выберите изображение</label>
                    </div>
                    <p style="margin-top: 20px; color: #666;">или перетащите файл сюда</p>
                    <button type="submit" id="processBtn">🚀 Удалить фон</button>
                </div>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 20px; text-align: center; color: #667eea;">
                    Обрабатываем изображение через AI...
                </p>
            </div>
            
            {% if status %}
            <div class="status {{ status_class }}">{{ status }}</div>
            {% endif %}
            
            <div class="result-area {% if output_image %}active{% endif %}">
                <div class="images-grid">
                    <div class="image-box">
                        <h4>Исходное изображение</h4>
                        {% if input_image %}
                        <img src="data:image/png;base64,{{ input_image }}" alt="Original">
                        {% endif %}
                    </div>
                    <div class="image-box">
                        <h4>Результат</h4>
                        {% if output_image %}
                        <img src="data:image/png;base64,{{ output_image }}" alt="Result">
                        <br>
                        <a href="data:image/png;base64,{{ output_image }}" download="result.png" class="download-btn">
                            💾 Скачать PNG
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
                document.querySelector('.file-input-label').textContent = '📎 ' + fileName;
            }
        });
        
        // Drag and drop
        const uploadArea = document.querySelector('.upload-area');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#667eea';
        });
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#e0e0e0';
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('file').files = files;
                document.querySelector('.file-input-label').textContent = '📎 ' + files[0].name;
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
                                         status='⚠️ API ключ не настроен. Показан оригинал.',
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
                                         status='✅ Фон успешно удален!',
                                         status_class='success',
                                         api_configured=True)
        else:
            return render_template_string(HTML_TEMPLATE,
                                         input_image=input_base64,
                                         status='❌ Ошибка при обработке через API',
                                         status_class='error',
                                         api_configured=True)
        
    except Exception as e:
        return render_template_string(HTML_TEMPLATE,
                                     status=f'Ошибка: {str(e)}',
                                     status_class='error')

def remove_background_fal(image):
    """
    Удаление фона через вашу натренированную LoRA модель на Fal.ai
    Используем FLUX Kontext для умного редактирования
    """
    try:
        # Конвертируем изображение в base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Подготавливаем запрос к Fal.ai
        headers = {
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Получаем путь к вашей LoRA модели из переменных окружения
        lora_path = os.environ.get('LORA_PATH', 
            'https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors')
        
        # Используем FLUX Kontext с вашей LoRA моделью
        data = {
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
        
        # Отправляем запрос на обработку
        response = requests.post(
            "https://fal.run/fal-ai/flux-kontext-lora",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            # Получаем URL обработанного изображения
            if 'images' in result and len(result['images']) > 0:
                img_url = result['images'][0]['url']
                # Загружаем результат
                img_response = requests.get(img_url)
                result_image = Image.open(io.BytesIO(img_response.content))
                return result_image
        
        print(f"API Error: {response.status_code} - {response.text}")
        
        # Fallback на обычное удаление фона если LoRA не сработала
        print("Trying fallback to BiRefNet...")
        data_fallback = {
            "image_url": f"data:image/png;base64,{img_base64}"
        }
        
        response = requests.post(
            "https://fal.run/fal-ai/birefnet",
            headers=headers,
            json=data_fallback,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'image' in result:
                img_response = requests.get(result['image'])
                result_image = Image.open(io.BytesIO(img_response.content))
                return result_image
        
        return None
        
    except Exception as e:
        print(f"Error calling Fal.ai API: {e}")
        return None

@app.route('/health')
def health():
    """Проверка состояния сервиса."""
    return jsonify({
        'status': 'healthy',
        'api_configured': bool(FAL_API_KEY),
        'service': 'ym-image-processor-api'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting API-based server on port {port}")
    print(f"📡 Fal.ai API configured: {bool(FAL_API_KEY)}")
    app.run(host='0.0.0.0', port=port, debug=False)