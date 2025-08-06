"""
Production Flask приложение для деплоя на внешний сервер.
"""

from flask import Flask, render_template_string, request, send_file, jsonify
from PIL import Image
import io
import base64
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.processors.background import BackgroundRemover

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# HTML шаблон
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>YM Image Processor</title>
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
        .content {
            padding: 30px;
        }
        .columns { 
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 30px;
        }
        @media (max-width: 768px) {
            .columns {
                grid-template-columns: 1fr;
            }
        }
        .column {
            text-align: center;
        }
        .image-box { 
            border: 3px dashed #e0e0e0;
            border-radius: 15px;
            padding: 30px;
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8f9fa;
            position: relative;
            overflow: hidden;
        }
        .image-box.has-image {
            border-color: #667eea;
            background: white;
        }
        img { 
            max-width: 100%;
            max-height: 400px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .upload-area {
            width: 100%;
            text-align: center;
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
        .status { 
            padding: 15px;
            margin: 20px 0;
            border-radius: 10px;
            font-weight: 500;
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
        .info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .loading {
            display: none;
            margin: 20px 0;
        }
        .loading.active {
            display: block;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        h4 {
            margin-bottom: 15px;
            color: #333;
            font-size: 1.2em;
        }
        .placeholder-text {
            color: #999;
            font-size: 1.1em;
        }
        .download-btn {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
            display: inline-block;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛍️ Yandex Market Image Processor</h1>
            <div class="subtitle">Профессиональное удаление фона с изображений товаров</div>
        </div>
        
        <div class="content">
            <div class="upload-area">
                <form method="POST" enctype="multipart/form-data" id="uploadForm">
                    <div class="file-input-wrapper">
                        <input type="file" name="file" id="file" accept="image/*" required>
                        <label for="file" class="file-input-label">📷 Выбрать изображение</label>
                    </div>
                    <br>
                    <button type="submit" id="processBtn">🚀 Удалить фон</button>
                </form>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 15px; color: #667eea;">Обрабатываем изображение...</p>
            </div>
            
            {% if status %}
            <div class="status {{ status_class }}">{{ status }}</div>
            {% endif %}
            
            <div class="columns">
                <div class="column">
                    <h4>Исходное изображение</h4>
                    <div class="image-box {% if input_image %}has-image{% endif %}">
                        {% if input_image %}
                        <img src="data:image/png;base64,{{ input_image }}" alt="Input">
                        {% else %}
                        <p class="placeholder-text">Загрузите изображение</p>
                        {% endif %}
                    </div>
                </div>
                
                <div class="column">
                    <h4>Результат</h4>
                    <div class="image-box {% if output_image %}has-image{% endif %}">
                        {% if output_image %}
                        <img src="data:image/png;base64,{{ output_image }}" alt="Output">
                        {% else %}
                        <p class="placeholder-text">Здесь появится результат</p>
                        {% endif %}
                    </div>
                    {% if output_image %}
                    <a href="data:image/png;base64,{{ output_image }}" download="processed.png" class="download-btn">
                        💾 Скачать результат
                    </a>
                    {% endif %}
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
    </script>
</body>
</html>
'''

# Инициализация процессора - ленивая загрузка для экономии памяти
processor = None

def init_processor():
    """Инициализация процессора при первом запросе."""
    global processor
    if processor is not None:
        return True
    try:
        # Используем u2netp - облегченная версия модели для экономии памяти
        processor = BackgroundRemover({
            'model': 'u2netp',  # Легкая версия модели (180MB вместо 340MB)
            'alpha_matting': False,  # Отключаем для экономии памяти
            'post_process': True,
            'min_object_size': 500,
            'use_cache': False  # Отключаем кеш для экономии памяти
        })
        print("✅ Процессор инициализирован с облегченной моделью")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False

@app.route('/')
def index():
    """Главная страница."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/', methods=['POST'])
def process():
    """Обработка загруженного изображения."""
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
        
        # Обрабатываем
        if processor is None:
            init_processor()
            
        result = processor.process(input_image)
        
        # Конвертируем результат в base64
        output_buffer = io.BytesIO()
        result.save(output_buffer, format='PNG')
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
        
        return render_template_string(HTML_TEMPLATE,
                                     input_image=input_base64,
                                     output_image=output_base64,
                                     status='✅ Обработка завершена успешно!',
                                     status_class='success')
        
    except Exception as e:
        return render_template_string(HTML_TEMPLATE,
                                     status=f'Ошибка: {str(e)}',
                                     status_class='error')

@app.route('/health')
def health():
    """Проверка состояния сервиса."""
    return jsonify({
        'status': 'healthy',
        'processor': processor is not None
    })

# НЕ инициализируем при запуске - только при первом запросе для экономии памяти

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Запуск сервера на порту {port}", flush=True)
    print(f"Сервер доступен на http://0.0.0.0:{port}", flush=True)
    # Запуск напрямую через Flask для Render
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)