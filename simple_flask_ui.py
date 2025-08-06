#!/usr/bin/env python3
"""Простой Flask UI для тестирования."""

from flask import Flask, render_template_string, request, send_file
from PIL import Image
import io
import base64
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

app = Flask(__name__)

# HTML шаблон
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>YM Image Processor</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .container { display: flex; gap: 20px; }
        .column { flex: 1; }
        .image-box { border: 2px dashed #ccc; padding: 20px; margin: 10px 0; min-height: 400px; text-align: center; }
        img { max-width: 100%; max-height: 400px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>🛍️ Yandex Market Image Processor</h1>
    <h3>Модуль удаления фона</h3>
    
    <div class="container">
        <div class="column">
            <h4>Исходное изображение</h4>
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="file" accept="image/*" required>
                <br><br>
                <button type="submit">🚀 Удалить фон</button>
            </form>
            
            {% if input_image %}
            <div class="image-box">
                <img src="data:image/png;base64,{{ input_image }}" alt="Input">
            </div>
            {% else %}
            <div class="image-box">
                <p>Загрузите изображение</p>
            </div>
            {% endif %}
        </div>
        
        <div class="column">
            <h4>Результат</h4>
            {% if status %}
            <div class="status {{ status_class }}">{{ status }}</div>
            {% endif %}
            
            {% if output_image %}
            <div class="image-box">
                <img src="data:image/png;base64,{{ output_image }}" alt="Output">
            </div>
            {% else %}
            <div class="image-box">
                <p>Результат появится здесь</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

# Пытаемся импортировать процессор
try:
    from src.processors.background import BackgroundRemover
    remover = BackgroundRemover()
    processor_available = True
except Exception as e:
    print(f"Ошибка импорта: {e}")
    processor_available = False
    remover = None

def image_to_base64(image):
    """Конвертация изображения в base64."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

@app.route('/', methods=['GET', 'POST'])
def index():
    context = {
        'input_image': None,
        'output_image': None,
        'status': None,
        'status_class': ''
    }
    
    if request.method == 'POST':
        if 'file' not in request.files:
            context['status'] = 'Файл не выбран'
            context['status_class'] = 'error'
        else:
            file = request.files['file']
            if file.filename == '':
                context['status'] = 'Файл не выбран'
                context['status_class'] = 'error'
            else:
                try:
                    # Загружаем изображение
                    image = Image.open(file.stream)
                    context['input_image'] = image_to_base64(image)
                    
                    if processor_available:
                        # Обрабатываем
                        result = remover.process(image)
                        context['output_image'] = image_to_base64(result)
                        context['status'] = '✅ Обработка завершена!'
                        context['status_class'] = 'success'
                    else:
                        context['status'] = '❌ Процессор недоступен'
                        context['status_class'] = 'error'
                        
                except Exception as e:
                    context['status'] = f'❌ Ошибка: {str(e)}'
                    context['status_class'] = 'error'
    
    return render_template_string(HTML_TEMPLATE, **context)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Запуск Flask UI")
    print("="*50)
    print(f"Процессор доступен: {'✓' if processor_available else '✗'}")
    # Используем порт 8080 чтобы избежать конфликта с AirPlay на macOS
    PORT = 8080
    print(f"\nОткройте браузер по адресу: http://localhost:{PORT}")
    print("Для остановки нажмите Ctrl+C")
    print("="*50 + "\n")
    
    app.run(debug=False, port=PORT, host='0.0.0.0')