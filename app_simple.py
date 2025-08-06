"""
Упрощенная версия для Render - минимальное потребление памяти
"""
import os
from flask import Flask, render_template_string, request, jsonify
from PIL import Image
import io
import base64

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>YM Image Processor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .status {
            padding: 15px;
            margin: 20px 0;
            border-radius: 10px;
            text-align: center;
        }
        .success {
            background: #d4edda;
            color: #155724;
        }
        .info {
            background: #d1ecf1;
            color: #0c5460;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 30px;
            cursor: pointer;
            font-size: 16px;
            display: block;
            margin: 20px auto;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .upload-box {
            border: 2px dashed #667eea;
            padding: 30px;
            text-align: center;
            border-radius: 10px;
            margin: 20px 0;
        }
        input[type="file"] {
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛍️ YM Image Processor</h1>
        <p style="text-align: center; color: #666;">Сервис удаления фона с изображений</p>
        
        <div class="status info">
            ℹ️ Сервис работает в упрощенном режиме для экономии ресурсов
        </div>
        
        <div class="upload-box">
            <form method="POST" action="/process" enctype="multipart/form-data">
                <p>Выберите изображение для обработки:</p>
                <input type="file" name="file" accept="image/*" required>
                <button type="submit">🚀 Обработать изображение</button>
            </form>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #666;">
            <small>Free план: обработка может занять 30-60 секунд</small>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Главная страница"""
    return render_template_string(HTML)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "ym-image-processor"})

@app.route('/process', methods=['POST'])
def process():
    """Обработка изображения - упрощенная версия"""
    try:
        if 'file' not in request.files:
            return "Файл не загружен", 400
            
        file = request.files['file']
        if file.filename == '':
            return "Файл не выбран", 400
            
        # Загружаем изображение
        img = Image.open(file.stream)
        
        # Здесь будет обработка когда добавим модель
        # Пока просто возвращаем информацию
        
        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    text-align: center;
                }}
                .success {{
                    background: #d4edda;
                    color: #155724;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
                a {{
                    display: inline-block;
                    margin: 20px;
                    padding: 15px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ Изображение получено!</h1>
                <div class="success">
                    <p>Размер: {img.size[0]}x{img.size[1]} пикселей</p>
                    <p>Формат: {img.format if img.format else 'Unknown'}</p>
                    <p>Режим: {img.mode}</p>
                </div>
                <p>Полная обработка будет доступна после оптимизации под Free план.</p>
                <a href="/">← Вернуться</a>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"Ошибка: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting server on port {port}", flush=True)
    app.run(host='0.0.0.0', port=port, debug=False)