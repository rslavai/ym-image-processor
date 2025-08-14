"""
Упрощенная версия для Render с облегченной моделью удаления фона
"""
import os
import gc
from flask import Flask, render_template_string, request, jsonify, send_file
from PIL import Image
import io
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# Глобальная переменная для модели
rembg_session = None

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

def init_model():
    """Инициализация модели при первом запросе"""
    global rembg_session
    if rembg_session is None:
        try:
            print("Загрузка модели...", flush=True)
            from rembg import new_session
            # Используем самую легкую модель
            rembg_session = new_session('u2netp')  # 180MB
            print("Модель загружена!", flush=True)
            return True
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}", flush=True)
            return False
    return True

@app.route('/process', methods=['POST'])
def process():
    """Обработка изображения с удалением фона"""
    try:
        if 'file' not in request.files:
            return "Файл не загружен", 400
            
        file = request.files['file']
        if file.filename == '':
            return "Файл не выбран", 400
            
        # Загружаем изображение
        img = Image.open(file.stream)
        
        # Уменьшаем размер если слишком большое (для экономии памяти)
        max_size = 1500
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Пробуем загрузить модель и обработать
        process_success = False
        result_img = None
        
        if init_model():
            try:
                from rembg import remove
                # Обрабатываем
                print(f"Обработка изображения {img.size}...", flush=True)
                result_img = remove(img, session=rembg_session)
                process_success = True
                print("Обработка завершена!", flush=True)
                
                # Очищаем память
                gc.collect()
            except Exception as e:
                print(f"Ошибка обработки: {e}", flush=True)
        # Формируем HTML ответ
        if process_success and result_img:
            # Конвертируем результат в base64 для отображения
            buffered = io.BytesIO()
            result_img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 1000px;
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
                    img {{
                        max-width: 100%;
                        max-height: 500px;
                        margin: 20px 0;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    }}
                    .download-btn {{
                        display: inline-block;
                        margin: 20px;
                        padding: 15px 30px;
                        background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
                        color: white;
                        text-decoration: none;
                        border-radius: 30px;
                        font-weight: bold;
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
                    <h1>🎉 Фон успешно удален!</h1>
                    <div class="success">
                        <p>✅ Обработка завершена успешно</p>
                        <p>Размер: {result_img.size[0]}x{result_img.size[1]} пикселей</p>
                    </div>
                    <img src="data:image/png;base64,{img_base64}" alt="Результат">
                    <br>
                    <a href="data:image/png;base64,{img_base64}" download="result.png" class="download-btn">
                        💾 Скачать результат
                    </a>
                    <a href="/">🔄 Обработать еще</a>
                </div>
            </body>
            </html>
            """
        else:
            # Если обработка не удалась, показываем информацию
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
                    .warning {{
                        background: #fff3cd;
                        color: #856404;
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
                    <h1>⚠️ Обработка временно недоступна</h1>
                    <div class="warning">
                        <p>Модель удаления фона не загружена</p>
                        <p>Размер изображения: {img.size[0]}x{img.size[1]} пикселей</p>
                        <p>Попробуйте еще раз через минуту</p>
                    </div>
                    <p><small>Free план имеет ограничения по памяти</small></p>
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