"""
YM Image Processor - Batch Processing Version
Processes multiple images with GPT-4 Vision analysis and smart positioning
"""

import os
import io
import json
import time
import base64
from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import threading
from queue import Queue

# Import our processors
from src.processors.batch_processor import BatchProcessor
from src.processors.smart_positioning import SmartPositioning

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max for batch
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Initialize batch processor
batch_processor = BatchProcessor()

# Progress tracking
progress_data = {}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>YM Batch Processor</title>
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
            padding: 40px 20px;
        }
        
        .container { 
            max-width: 1200px; 
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 48px;
        }
        
        h1 { 
            font-size: 3rem;
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
        }
        
        .subtitle {
            color: #86868b;
            font-size: 1.2rem;
        }
        
        .tabs {
            display: flex;
            gap: 20px;
            margin-bottom: 40px;
            border-bottom: 1px solid #e5e5e5;
        }
        
        .tab {
            padding: 12px 24px;
            color: #86868b;
            text-decoration: none;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
            font-weight: 500;
        }
        
        .tab.active {
            color: #1d1d1f;
            border-bottom-color: #1d1d1f;
        }
        
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
            margin-bottom: 32px;
        }
        
        .upload-zone {
            background: rgba(255, 255, 255, 0.5);
            border: 2px dashed rgba(0, 0, 0, 0.1);
            border-radius: 16px;
            padding: 60px 40px;
            text-align: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            position: relative;
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
        
        .upload-icon {
            width: 64px;
            height: 64px;
            margin: 0 auto 20px;
            opacity: 0.3;
        }
        
        input[type="file"] {
            position: absolute;
            left: -9999px;
        }
        
        .file-label {
            display: inline-block;
            padding: 14px 36px;
            background: #1d1d1f;
            color: white;
            border-radius: 100px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .file-label:hover {
            background: #000000;
            transform: scale(1.05);
        }
        
        .file-count {
            margin-top: 20px;
            color: #86868b;
            font-size: 0.95rem;
        }
        
        .preview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 16px;
            margin-top: 32px;
            max-height: 400px;
            overflow-y: auto;
            padding: 4px;
        }
        
        .preview-item {
            position: relative;
            aspect-ratio: 1;
            border-radius: 12px;
            overflow: hidden;
            background: #f5f5f7;
        }
        
        .preview-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .preview-item .status {
            position: absolute;
            top: 8px;
            right: 8px;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }
        
        .status.pending { background: #ffc107; }
        .status.processing { background: #2196f3; }
        .status.success { background: #4caf50; }
        .status.error { background: #f44336; }
        
        button.process-btn { 
            background: #1d1d1f;
            color: #ffffff;
            padding: 16px 48px;
            border: none;
            cursor: pointer;
            border-radius: 100px;
            font-size: 1.1rem;
            font-weight: 500;
            margin-top: 32px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: -0.01em;
            width: 100%;
        }
        
        button.process-btn:hover { 
            background: #000000;
            transform: scale(1.02);
        }
        
        button.process-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
            transform: none;
        }
        
        .progress-container {
            margin-top: 48px;
            display: none;
        }
        
        .progress-container.active {
            display: block;
        }
        
        .overall-progress {
            margin-bottom: 32px;
        }
        
        .progress-bar {
            height: 8px;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin: 12px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: #1d1d1f;
            transition: width 0.3s ease;
            border-radius: 4px;
        }
        
        .progress-text {
            color: #86868b;
            font-size: 0.9rem;
            margin-top: 8px;
        }
        
        .file-progress-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .file-progress-item {
            display: flex;
            align-items: center;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            background: rgba(255, 255, 255, 0.5);
        }
        
        .file-progress-name {
            flex: 1;
            font-size: 0.9rem;
            color: #1d1d1f;
        }
        
        .file-progress-status {
            padding: 4px 12px;
            border-radius: 100px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .status-pending { background: #fff3cd; color: #856404; }
        .status-processing { background: #cce5ff; color: #004085; }
        .status-success { background: #d4edda; color: #155724; }
        .status-error { background: #f8d7da; color: #721c24; }
        
        .download-section {
            margin-top: 48px;
            text-align: center;
            display: none;
        }
        
        .download-section.active {
            display: block;
        }
        
        .download-btn {
            display: inline-block;
            padding: 16px 48px;
            background: #34c759;
            color: white;
            text-decoration: none;
            border-radius: 100px;
            font-weight: 500;
            font-size: 1.1rem;
            transition: all 0.3s;
        }
        
        .download-btn:hover {
            background: #30b350;
            transform: scale(1.05);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 24px;
            margin: 32px 0;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.5);
            padding: 24px;
            border-radius: 16px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 600;
            color: #1d1d1f;
        }
        
        .stat-label {
            color: #86868b;
            font-size: 0.9rem;
            margin-top: 8px;
        }
        
        .options {
            margin: 32px 0;
            padding: 24px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 16px;
        }
        
        .option-item {
            display: flex;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .option-item:last-child {
            margin-bottom: 0;
        }
        
        .option-item input[type="checkbox"] {
            width: 20px;
            height: 20px;
            margin-right: 12px;
        }
        
        .option-item label {
            color: #1d1d1f;
            font-size: 0.95rem;
        }
        
        .option-description {
            color: #86868b;
            font-size: 0.85rem;
            margin-left: 32px;
            margin-top: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>YM Batch Processor</h1>
            <p class="subtitle">Умная обработка изображений с AI анализом</p>
        </div>
        
        <div class="tabs">
            <a href="/single" class="tab">Одиночная обработка</a>
            <a href="/" class="tab active">Пакетная обработка</a>
            <a href="/history" class="tab">История</a>
        </div>
        
        <div class="glass-card">
            <form id="batchForm" enctype="multipart/form-data">
                <div class="upload-zone" id="uploadZone">
                    <svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <input type="file" id="fileInput" multiple accept="image/*">
                    <label for="fileInput" class="file-label">Выберите изображения</label>
                    <p class="file-count" id="fileCount">или перетащите файлы сюда (до 100 штук)</p>
                </div>
                
                <div class="preview-grid" id="previewGrid"></div>
                
                <div class="options">
                    <h3 style="margin-bottom: 20px; color: #1d1d1f;">Опции обработки</h3>
                    <div class="option-item">
                        <input type="checkbox" id="enhanceImages" name="enhance">
                        <label for="enhanceImages">Умная обработка</label>
                    </div>
                    <p class="option-description">Автокоррекция экспозиции, усиление резкости, нормализация освещения</p>
                    
                    <div class="option-item" style="margin-top: 16px;">
                        <input type="checkbox" id="debugMode" name="debug">
                        <label for="debugMode">Режим отладки</label>
                    </div>
                    <p class="option-description">Показать сетку позиционирования на финальных изображениях</p>
                </div>
                
                <button type="submit" class="process-btn" id="processBtn" disabled>
                    Обработать изображения
                </button>
            </form>
        </div>
        
        <div class="progress-container" id="progressContainer">
            <div class="glass-card">
                <div class="overall-progress">
                    <h3>Общий прогресс</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" id="overallProgress" style="width: 0%"></div>
                    </div>
                    <p class="progress-text" id="progressText">0 из 0 обработано</p>
                </div>
                
                <div class="file-progress-list" id="fileProgressList"></div>
            </div>
        </div>
        
        <div class="download-section" id="downloadSection">
            <div class="glass-card">
                <h2 style="margin-bottom: 24px;">Обработка завершена!</h2>
                
                <div class="stats" id="stats"></div>
                
                <a href="#" class="download-btn" id="downloadBtn">
                    Скачать результаты (ZIP)
                </a>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFiles = [];
        let processingStatus = {};
        
        // File input handling
        const fileInput = document.getElementById('fileInput');
        const uploadZone = document.getElementById('uploadZone');
        const previewGrid = document.getElementById('previewGrid');
        const fileCount = document.getElementById('fileCount');
        const processBtn = document.getElementById('processBtn');
        
        fileInput.addEventListener('change', handleFiles);
        
        // Drag and drop
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
            const files = Array.from(e.dataTransfer.files);
            handleFileSelection(files);
        });
        
        function handleFiles(e) {
            const files = Array.from(e.target.files);
            handleFileSelection(files);
        }
        
        function handleFileSelection(files) {
            // Filter only images
            const imageFiles = files.filter(file => file.type.startsWith('image/'));
            
            // Limit to 100 files
            if (imageFiles.length > 100) {
                alert('Максимум 100 файлов за раз');
                imageFiles.splice(100);
            }
            
            selectedFiles = imageFiles;
            updateFileCount();
            showPreviews();
            
            processBtn.disabled = selectedFiles.length === 0;
        }
        
        function updateFileCount() {
            if (selectedFiles.length > 0) {
                fileCount.textContent = `Выбрано файлов: ${selectedFiles.length}`;
            } else {
                fileCount.textContent = 'или перетащите файлы сюда (до 100 штук)';
            }
        }
        
        function showPreviews() {
            previewGrid.innerHTML = '';
            
            selectedFiles.forEach((file, index) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const div = document.createElement('div');
                    div.className = 'preview-item';
                    div.id = `preview-${index}`;
                    div.innerHTML = `
                        <img src="${e.target.result}" alt="${file.name}">
                        <div class="status pending" id="status-${index}"></div>
                    `;
                    previewGrid.appendChild(div);
                };
                reader.readAsDataURL(file);
            });
        }
        
        // Form submission
        document.getElementById('batchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (selectedFiles.length === 0) {
                alert('Выберите файлы для обработки');
                return;
            }
            
            // Prepare form data
            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append('files', file);
            });
            
            // Add options
            formData.append('enhance', document.getElementById('enhanceImages').checked);
            formData.append('debug', document.getElementById('debugMode').checked);
            
            // Disable button and show progress
            processBtn.disabled = true;
            document.getElementById('progressContainer').classList.add('active');
            
            // Start processing
            try {
                const response = await fetch('/process_batch', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const result = await response.json();
                    
                    // Start polling for progress
                    pollProgress(result.batch_id);
                } else {
                    alert('Ошибка при обработке');
                    processBtn.disabled = false;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Ошибка при отправке файлов');
                processBtn.disabled = false;
            }
        });
        
        async function pollProgress(batchId) {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`/progress/${batchId}`);
                    const data = await response.json();
                    
                    updateProgress(data);
                    
                    if (data.completed) {
                        clearInterval(interval);
                        showDownloadSection(data);
                    }
                } catch (error) {
                    console.error('Error polling progress:', error);
                }
            }, 1000);
        }
        
        function updateProgress(data) {
            const progressFill = document.getElementById('overallProgress');
            const progressText = document.getElementById('progressText');
            const fileList = document.getElementById('fileProgressList');
            
            const percent = (data.processed / data.total) * 100;
            progressFill.style.width = percent + '%';
            progressText.textContent = `${data.processed} из ${data.total} обработано`;
            
            // Update file list
            if (data.files) {
                fileList.innerHTML = '';
                data.files.forEach(file => {
                    const div = document.createElement('div');
                    div.className = 'file-progress-item';
                    div.innerHTML = `
                        <span class="file-progress-name">${file.name}</span>
                        <span class="file-progress-status status-${file.status}">${getStatusText(file.status)}</span>
                    `;
                    fileList.appendChild(div);
                    
                    // Update preview status
                    const previewStatus = document.getElementById(`status-${file.index}`);
                    if (previewStatus) {
                        previewStatus.className = `status ${file.status}`;
                    }
                });
            }
        }
        
        function getStatusText(status) {
            const texts = {
                'pending': 'Ожидает',
                'processing': 'Обработка',
                'success': 'Готово',
                'error': 'Ошибка'
            };
            return texts[status] || status;
        }
        
        function showDownloadSection(data) {
            const downloadSection = document.getElementById('downloadSection');
            const stats = document.getElementById('stats');
            const downloadBtn = document.getElementById('downloadBtn');
            
            // Show stats
            stats.innerHTML = `
                <div class="stat-card">
                    <div class="stat-value">${data.total}</div>
                    <div class="stat-label">Всего файлов</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.successful}</div>
                    <div class="stat-label">Успешно</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.failed}</div>
                    <div class="stat-label">Ошибок</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${Math.round(data.processing_time)}с</div>
                    <div class="stat-label">Время обработки</div>
                </div>
            `;
            
            // Set download link
            downloadBtn.href = `/download/${data.batch_id}`;
            
            downloadSection.classList.add('active');
        }
    </script>
</body>
</html>
'''

# Routes
@app.route('/')
def index():
    """Main batch processing page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/single')
def single_mode():
    """Redirect to single processing app"""
    # For now, show message that single mode is integrated
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Single Mode</title>
        <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body { 
                font-family: 'Syne', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background: #f5f5f7;
            }
            .message {
                text-align: center;
                padding: 40px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            h2 { color: #1d1d1f; margin-bottom: 16px; }
            p { color: #86868b; margin-bottom: 24px; }
            a {
                display: inline-block;
                padding: 12px 32px;
                background: #007aff;
                color: white;
                text-decoration: none;
                border-radius: 100px;
                font-weight: 500;
            }
        </style>
    </head>
    <body>
        <div class="message">
            <h2>Одиночная обработка</h2>
            <p>Для обработки одного изображения используйте пакетный режим<br>и загрузите только один файл</p>
            <a href="/">Перейти к обработке</a>
        </div>
    </body>
    </html>
    '''

@app.route('/process_batch', methods=['POST'])
def process_batch():
    """Process batch of images"""
    try:
        files = request.files.getlist('files')
        enhance = request.form.get('enhance') == 'true'
        debug = request.form.get('debug') == 'true'
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        # Generate batch ID
        batch_id = f"batch_{int(time.time())}"
        progress_data[batch_id] = {
            'total': len(files),
            'processed': 0,
            'files': [],
            'completed': False
        }
        
        # Convert files to data before background processing
        file_data = []
        for file in files:
            file_data.append({
                'filename': file.filename,
                'content': file.stream.read(),
                'content_type': file.content_type
            })
            file.stream.seek(0)  # Reset for any other use
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_files_background,
            args=(file_data, batch_id, enhance, debug)
        )
        thread.start()
        
        return jsonify({'batch_id': batch_id, 'total': len(files)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

class FileDataWrapper:
    """Wrapper to mimic Flask FileStorage for our file data"""
    def __init__(self, file_data):
        self.filename = file_data['filename']
        self.content_type = file_data['content_type']
        self.stream = io.BytesIO(file_data['content'])

def process_files_background(file_data_list, batch_id, enhance, debug):
    """Background processing of files"""
    # Convert file data back to file-like objects
    files = [FileDataWrapper(file_data) for file_data in file_data_list]
    try:
        # Set debug mode if requested
        if debug:
            batch_processor.positioner.set_debug_mode(True)
        
        def progress_callback(data):
            progress_data[batch_id]['processed'] = data['processed']
            progress_data[batch_id]['current_file'] = data['current_file']
            
            # Update file status
            file_status = {
                'name': data['current_file'],
                'status': data['status'],
                'index': data['processed'] - 1
            }
            
            # Update or append file status
            existing = False
            for i, f in enumerate(progress_data[batch_id]['files']):
                if f['name'] == data['current_file']:
                    progress_data[batch_id]['files'][i] = file_status
                    existing = True
                    break
            
            if not existing:
                progress_data[batch_id]['files'].append(file_status)
        
        # Process batch
        result = batch_processor.process_batch(files, progress_callback)
        
        # Mark as completed
        progress_data[batch_id]['completed'] = True
        progress_data[batch_id]['result'] = result
        progress_data[batch_id]['successful'] = result['successful']
        progress_data[batch_id]['failed'] = result['failed']
        progress_data[batch_id]['zip_path'] = result['zip_path']
        progress_data[batch_id]['processing_time'] = time.time() - int(batch_id.split('_')[1])
        
    except Exception as e:
        print(f"Error in background processing: {e}")
        progress_data[batch_id]['completed'] = True
        progress_data[batch_id]['error'] = str(e)

@app.route('/progress/<batch_id>')
def get_progress(batch_id):
    """Get processing progress"""
    if batch_id in progress_data:
        return jsonify(progress_data[batch_id])
    return jsonify({'error': 'Batch not found'}), 404

@app.route('/download/<batch_id>')
def download_results(batch_id):
    """Download ZIP archive of results"""
    if batch_id in progress_data and progress_data[batch_id].get('completed'):
        zip_path = progress_data[batch_id].get('zip_path')
        if zip_path and os.path.exists(zip_path):
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f'{batch_id}_results.zip',
                mimetype='application/zip'
            )
    return "File not found", 404

@app.route('/history')
def history():
    """View processing history"""
    try:
        history_data = batch_processor.get_history(limit=100)
        return render_template_string(HISTORY_TEMPLATE, history=history_data)
    except Exception as e:
        return f"Error loading history: {str(e)}", 500

# History template (simplified for now)
HISTORY_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Processing History</title>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Syne', sans-serif;
            padding: 40px;
            background: #f5f5f7;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #1d1d1f; margin-bottom: 32px; }
        .back-link { 
            display: inline-block;
            margin-bottom: 24px;
            color: #007aff;
            text-decoration: none;
        }
        table {
            width: 100%;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e5e5;
        }
        th {
            background: #f5f5f7;
            font-weight: 600;
        }
        .status-success { color: #34c759; }
        .status-error { color: #ff3b30; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Вернуться к обработке</a>
        <h1>История обработки</h1>
        <table>
            <thead>
                <tr>
                    <th>Batch ID</th>
                    <th>Файл</th>
                    <th>Категория</th>
                    <th>Тип</th>
                    <th>Ориентация</th>
                    <th>Статус</th>
                    <th>Время</th>
                </tr>
            </thead>
            <tbody>
                {% for item in history %}
                <tr>
                    <td>{{ item.batch_id }}</td>
                    <td>{{ item.filename }}</td>
                    <td>{{ item.category or '-' }}</td>
                    <td>{{ item.product_type or '-' }}</td>
                    <td>{{ item.orientation or '-' }}</td>
                    <td class="status-{{ item.status }}">{{ item.status }}</td>
                    <td>{{ item.upload_time }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
'''

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ym-batch-processor',
        'openai_configured': bool(os.environ.get('OPENAI_API_KEY')),
        'fal_configured': bool(os.environ.get('FAL_API_KEY'))
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('processed', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Batch Processor on port {port}")
    print(f"OpenAI API configured: {bool(os.environ.get('OPENAI_API_KEY'))}")
    print(f"Fal.ai API configured: {bool(os.environ.get('FAL_API_KEY'))}")
    app.run(host='0.0.0.0', port=port, debug=False)