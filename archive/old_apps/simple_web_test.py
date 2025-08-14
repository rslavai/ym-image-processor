#!/usr/bin/env python3
"""Простое веб-приложение для тестирования удаления фона."""

from flask import Flask, render_template_string, request, send_file
from PIL import Image
import io
import base64
import sys
from pathlib import Path

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent))

try:
    from src.processors.background import BackgroundRemover
    remover = BackgroundRemover()
    print("✓ BackgroundRemover загружен успешно")
except Exception as e:
    print(f"❌ Ошибка загрузки BackgroundRemover: {e}")
    remover = None

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>YM Image Processor - Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            margin: 20px 0;
        }
        .upload-area:hover {
            border-color: #999;
            background-color: #fafafa;
        }
        input[type="file"] {
            display: none;
        }
        .upload-btn {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .upload-btn:hover {
            background-color: #45a049;
        }
        .process-btn {
            background-color: #2196F3;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 18px;
            margin: 20px auto;
            display: block;
        }
        .process-btn:hover {
            background-color: #1976D2;
        }
        .process-btn:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .image-container {
            display: flex;
            justify-content: space-around;
            gap: 20px;
            margin-top: 30px;
        }
        .image-box {
            flex: 1;
            text-align: center;
        }
        .image-box img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .status {
            text-align: center;
            margin: 20px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .status.success {
            background-color: #d4edda;
            color: #155724;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
        }
        .download-btn {
            background-color: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛍️ Yandex Market Image Processor</h1>
        <p style="text-align: center; color: #666;">Тест модуля удаления фона</p>
        
        <div class="upload-area" onclick="document.getElementById('file-input').click();">
            <p>Нажмите для выбора изображения или перетащите файл сюда</p>
            <input type="file" id="file-input" accept="image/*" onchange="handleFileSelect(event)">
            <button class="upload-btn">Выбрать файл</button>
        </div>
        
        <div id="status"></div>
        
        <button class="process-btn" id="process-btn" onclick="processImage()" disabled>
            🚀 Удалить фон
        </button>
        
        <div class="image-container">
            <div class="image-box">
                <h3>Исходное изображение</h3>
                <div id="original-image"></div>
            </div>
            <div class="image-box">
                <h3>Результат</h3>
                <div id="result-image"></div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        
        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file && file.type.startsWith('image/')) {
                selectedFile = file;
                displayImage(file);
                document.getElementById('process-btn').disabled = false;
                showStatus('Изображение загружено. Нажмите "Удалить фон" для обработки.', 'success');
            } else {
                showStatus('Пожалуйста, выберите изображение.', 'error');
            }
        }
        
        function displayImage(file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('original-image').innerHTML = 
                    '<img src="' + e.target.result + '" style="max-height: 400px;">';
            };
            reader.readAsDataURL(file);
        }
        
        function showStatus(message, type) {
            const statusEl = document.getElementById('status');
            statusEl.className = 'status ' + type;
            statusEl.textContent = message;
        }
        
        function processImage() {
            if (!selectedFile) return;
            
            const formData = new FormData();
            formData.append('image', selectedFile);
            
            document.getElementById('process-btn').disabled = true;
            showStatus('Обработка изображения...', 'success');
            
            fetch('/process', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('result-image').innerHTML = 
                        '<img src="data:image/png;base64,' + data.image + '" style="max-height: 400px;">' +
                        '<br><a href="data:image/png;base64,' + data.image + '" download="result.png" class="download-btn">💾 Скачать</a>';
                    showStatus('✅ Обработка завершена успешно!', 'success');
                } else {
                    showStatus('❌ Ошибка: ' + data.error, 'error');
                }
                document.getElementById('process-btn').disabled = false;
            })
            .catch(error => {
                showStatus('❌ Ошибка сети: ' + error, 'error');
                document.getElementById('process-btn').disabled = false;
            });
        }
        
        // Drag and drop
        const uploadArea = document.querySelector('.upload-area');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.backgroundColor = '#f0f0f0';
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.backgroundColor = '';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.backgroundColor = '';
            
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                selectedFile = file;
                displayImage(file);
                document.getElementById('process-btn').disabled = false;
                showStatus('Изображение загружено. Нажмите "Удалить фон" для обработки.', 'success');
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    try:
        if 'image' not in request.files:
            return {'success': False, 'error': 'Изображение не найдено'}
        
        file = request.files['image']
        if file.filename == '':
            return {'success': False, 'error': 'Файл не выбран'}
        
        # Загружаем изображение
        image = Image.open(file.stream).convert('RGB')
        
        if remover is None:
            return {'success': False, 'error': 'Процессор не инициализирован'}
        
        # Обрабатываем
        result = remover.process(image)
        
        # Конвертируем в base64
        buffered = io.BytesIO()
        result.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return {'success': True, 'image': img_base64}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    print("🚀 Запуск веб-приложения...")
    print("Откройте браузер по адресу: http://localhost:5001")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")