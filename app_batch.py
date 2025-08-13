"""
YM Image Processor - Batch Processing Version
Processes multiple images with GPT-4 Vision analysis and smart positioning
"""

import os
import io
import json
import time
import base64
from pathlib import Path
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
single_progress_data = {}

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
    """Single image processing with detailed steps"""
    return render_template_string(SINGLE_TEMPLATE)

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
        batch_processor.positioner.set_debug_mode(debug)
        
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
        progress_data[batch_id]['batch_id'] = result['batch_id']  # Add batch_id to progress data
        progress_data[batch_id]['processing_time'] = time.time() - int(batch_id.split('_')[1])
        
        print(f"Batch {batch_id} completed. ZIP path: {result['zip_path']}")  # Debug log
        
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
    # First check in-memory progress data
    if batch_id in progress_data and progress_data[batch_id].get('completed'):
        zip_path = progress_data[batch_id].get('zip_path')
        if zip_path and os.path.exists(zip_path):
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f'{batch_id}_results.zip',
                mimetype='application/zip'
            )
    
    # If not found in memory, check database
    batch_info = batch_processor.get_batch_by_id(batch_id)
    if batch_info and batch_info.get('zip_path'):
        zip_path = batch_info['zip_path']
        if os.path.exists(zip_path):
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
        history_data = batch_processor.get_batch_history(limit=50)
        return render_template_string(HISTORY_TEMPLATE, history=history_data)
    except Exception as e:
        return f"Error loading history: {str(e)}", 500

# Single processing template
SINGLE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>YM Single Processor</title>
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
            margin-bottom: 32px;
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
        
        .options {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .option-group {
            background: rgba(255, 255, 255, 0.3);
            padding: 24px;
            border-radius: 16px;
        }
        
        .option-group h3 {
            color: #1d1d1f;
            margin-bottom: 16px;
            font-size: 1.1rem;
        }
        
        .option-item {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .option-item:last-child {
            margin-bottom: 0;
        }
        
        .option-item input[type="checkbox"] {
            width: 18px;
            height: 18px;
            margin-right: 10px;
        }
        
        .option-item label {
            color: #1d1d1f;
            font-size: 0.9rem;
            cursor: pointer;
        }
        
        .prompt-area {
            margin-top: 16px;
        }
        
        .prompt-area textarea {
            width: 100%;
            min-height: 80px;
            padding: 12px;
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            font-family: inherit;
            font-size: 0.9rem;
            resize: vertical;
        }
        
        .prompt-area textarea:focus {
            outline: none;
            border-color: #1d1d1f;
        }
        
        .process-btn {
            background: #1d1d1f;
            color: #ffffff;
            padding: 16px 48px;
            border: none;
            cursor: pointer;
            border-radius: 100px;
            font-size: 1.1rem;
            font-weight: 500;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: -0.01em;
            width: 100%;
        }
        
        .process-btn:hover {
            background: #000000;
            transform: scale(1.02);
        }
        
        .process-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
            transform: none;
        }
        
        .processing-section {
            display: none;
            margin-top: 48px;
        }
        
        .processing-section.active {
            display: block;
        }
        
        .step-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            margin-top: 32px;
        }
        
        .step-card {
            background: rgba(255, 255, 255, 0.8);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            border: 2px solid transparent;
            transition: all 0.3s;
        }
        
        .step-card.active {
            border-color: #1d1d1f;
            background: rgba(255, 255, 255, 0.95);
        }
        
        .step-card.completed {
            border-color: #34c759;
            background: rgba(52, 199, 89, 0.1);
        }
        
        .step-card.error {
            border-color: #ff3b30;
            background: rgba(255, 59, 48, 0.1);
        }
        
        .step-title {
            color: #1d1d1f;
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        .step-image {
            width: 100%;
            max-width: 350px;
            height: 350px;
            border-radius: 12px;
            object-fit: cover;
            background: #f5f5f7;
            margin-bottom: 16px;
        }
        
        .step-status {
            font-size: 0.9rem;
            padding: 8px 16px;
            border-radius: 100px;
            font-weight: 500;
        }
        
        .status-pending {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-processing {
            background: #cce5ff;
            color: #004085;
        }
        
        .status-completed {
            background: #d4edda;
            color: #155724;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .analysis-data {
            background: rgba(0, 0, 0, 0.05);
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            text-align: left;
            font-size: 0.8rem;
            color: #666;
            white-space: pre-wrap;
            font-family: monospace;
        }
        
        .download-buttons {
            display: flex;
            gap: 12px;
            margin-top: 16px;
            justify-content: center;
        }
        
        .download-btn {
            padding: 8px 16px;
            background: #34c759;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .download-btn:hover {
            background: #30b350;
            transform: scale(1.05);
        }
        
        .download-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>YM Single Processor</h1>
            <p class="subtitle">Детальная обработка одного изображения с показом всех этапов</p>
        </div>
        
        <div class="tabs">
            <a href="/single" class="tab active">Одиночная обработка</a>
            <a href="/" class="tab">Пакетная обработка</a>
            <a href="/history" class="tab">История</a>
        </div>
        
        <div class="glass-card">
            <form id="singleForm" enctype="multipart/form-data">
                <div class="upload-zone" id="uploadZone">
                    <svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <input type="file" id="fileInput" accept="image/*">
                    <label for="fileInput" class="file-label">Выберите изображение</label>
                    <p style="margin-top: 16px; color: #86868b;">или перетащите файл сюда</p>
                </div>
                
                <div class="options">
                    <div class="option-group">
                        <h3>Опции обработки</h3>
                        <div class="option-item">
                            <input type="checkbox" id="enhanceImages" name="enhance">
                            <label for="enhanceImages">Умная обработка</label>
                        </div>
                        <div class="option-item">
                            <input type="checkbox" id="debugMode" name="debug">
                            <label for="debugMode">Режим отладки</label>
                        </div>
                    </div>
                    
                    <div class="option-group">
                        <h3>Настройки LoRA</h3>
                        <div class="option-item">
                            <label for="loraVersion" style="margin-right: 12px; color: #1d1d1f;">Версия LoRA:</label>
                            <select id="loraVersion" name="loraVersion" style="padding: 6px 12px; border: 1px solid #e5e5e5; border-radius: 6px; background: white;">
                                <option value="v1">V1 (Стандартная)</option>
                                <option value="v2">V2 (Улучшенная)</option>
                            </select>
                        </div>
                        <div class="option-item">
                            <input type="checkbox" id="customPrompt" name="customPrompt">
                            <label for="customPrompt">Использовать свой промпт</label>
                        </div>
                        <div class="prompt-area" id="promptArea" style="display: none;">
                            <textarea id="customPromptText" placeholder="Введите свой промпт для LoRA модели. Если оставить пустым, будет использован промпт по умолчанию."></textarea>
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="process-btn" id="processBtn" disabled>
                    Обработать изображение
                </button>
            </form>
        </div>
        
        <div class="processing-section" id="processingSection">
            <div class="glass-card">
                <h2 style="text-align: center; margin-bottom: 32px;">Этапы обработки</h2>
                
                <div class="step-container">
                    <div class="step-card" id="step-original">
                        <h3 class="step-title">1. Оригинальное изображение</h3>
                        <img class="step-image" id="img-original" src="" alt="Оригинал">
                        <div class="step-status status-pending" id="status-original">Загрузка...</div>
                        <div class="download-buttons">
                            <a href="#" class="download-btn" id="download-original" style="display: none;">Скачать</a>
                        </div>
                    </div>
                    
                    <div class="step-card" id="step-analysis">
                        <h3 class="step-title">2. GPT-4 Анализ</h3>
                        <div style="display: flex; flex-direction: column; align-items: center; height: 350px; justify-content: center;">
                            <div style="font-size: 2rem;">🤖</div>
                            <div style="margin-top: 12px;">AI анализ продукта</div>
                        </div>
                        <div class="step-status status-pending" id="status-analysis">Ожидание</div>
                        <div class="analysis-data" id="analysis-data" style="display: none;"></div>
                    </div>
                    
                    <div class="step-card" id="step-background">
                        <h3 class="step-title">3. Удаление фона</h3>
                        <img class="step-image" id="img-background" src="" alt="Без фона">
                        <div class="step-status status-pending" id="status-background">Ожидание</div>
                        <div class="download-buttons">
                            <a href="#" class="download-btn" id="download-background" style="display: none;">Скачать</a>
                        </div>
                    </div>
                    
                    <div class="step-card" id="step-final">
                        <h3 class="step-title">4. Финальный результат</h3>
                        <img class="step-image" id="img-final" src="" alt="Результат">
                        <div class="step-status status-pending" id="status-final">Ожидание</div>
                        <div class="download-buttons">
                            <a href="#" class="download-btn" id="download-final" style="display: none;">Скачать</a>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 32px;">
                    <div id="promptUsed" style="background: rgba(0,0,0,0.05); padding: 16px; border-radius: 12px; font-family: monospace; font-size: 0.9rem; text-align: left; display: none;">
                        <div style="margin-bottom: 8px;">
                            <strong>Версия LoRA:</strong> <span id="loraVersionText" style="background: #34c759; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem;"></span>
                        </div>
                        <strong>Промпт, отправленный в LoRA:</strong><br>
                        <span id="promptText"></span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        let currentProcessingId = null;
        
        // DOM elements
        const fileInput = document.getElementById('fileInput');
        const uploadZone = document.getElementById('uploadZone');
        const processBtn = document.getElementById('processBtn');
        const customPromptCheck = document.getElementById('customPrompt');
        const promptArea = document.getElementById('promptArea');
        const processingSection = document.getElementById('processingSection');
        
        // File handling
        fileInput.addEventListener('change', handleFileSelect);
        
        // Custom prompt toggle
        customPromptCheck.addEventListener('change', function() {
            promptArea.style.display = this.checked ? 'block' : 'none';
        });
        
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
            if (files.length > 0 && files[0].type.startsWith('image/')) {
                selectedFile = files[0];
                updateFileDisplay();
            }
        });
        
        function handleFileSelect(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                selectedFile = file;
                updateFileDisplay();
            }
        }
        
        function updateFileDisplay() {
            if (selectedFile) {
                const fileName = selectedFile.name;
                uploadZone.innerHTML = `
                    <svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p style="color: #1d1d1f; font-weight: 500; margin-top: 12px;">${fileName}</p>
                    <p style="color: #86868b; font-size: 0.9rem; margin-top: 8px;">Нажмите для выбора другого файла</p>
                `;
                processBtn.disabled = false;
            }
        }
        
        // Form submission
        document.getElementById('singleForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!selectedFile) {
                alert('Выберите изображение для обработки');
                return;
            }
            
            processBtn.disabled = true;
            processingSection.classList.add('active');
            
            // Show original image
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('img-original').src = e.target.result;
                setStepStatus('original', 'completed', 'Загружено');
                document.getElementById('step-original').classList.add('completed');
            };
            reader.readAsDataURL(selectedFile);
            
            // Prepare form data
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('enhance', document.getElementById('enhanceImages').checked);
            formData.append('debug', document.getElementById('debugMode').checked);
            formData.append('customPrompt', document.getElementById('customPrompt').checked);
            formData.append('customPromptText', document.getElementById('customPromptText').value);
            formData.append('loraVersion', document.getElementById('loraVersion').value);
            
            try {
                // Start processing
                setStepStatus('analysis', 'processing', 'Анализ...');
                document.getElementById('step-analysis').classList.add('active');
                
                const response = await fetch('/process_single', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const result = await response.json();
                    currentProcessingId = result.processing_id;
                    
                    // Poll for results
                    pollSingleProgress(result.processing_id);
                } else {
                    throw new Error('Processing failed');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Ошибка при обработке изображения');
                processBtn.disabled = false;
            }
        });
        
        async function pollSingleProgress(processingId) {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`/single_progress/${processingId}`);
                    const data = await response.json();
                    
                    updateSingleProgress(data);
                    
                    if (data.completed) {
                        clearInterval(interval);
                        processBtn.disabled = false;
                    }
                } catch (error) {
                    console.error('Error polling progress:', error);
                    clearInterval(interval);
                    processBtn.disabled = false;
                }
            }, 1000);
        }
        
        function updateSingleProgress(data) {
            // Update analysis step
            if (data.analysis_completed) {
                setStepStatus('analysis', 'completed', 'Завершен');
                document.getElementById('step-analysis').classList.remove('active');
                document.getElementById('step-analysis').classList.add('completed');
                
                if (data.analysis_data) {
                    document.getElementById('analysis-data').textContent = JSON.stringify(data.analysis_data, null, 2);
                    document.getElementById('analysis-data').style.display = 'block';
                }
                
                // Show used prompt and LoRA version
                if (data.prompt_used) {
                    document.getElementById('promptUsed').style.display = 'block';
                    document.getElementById('promptText').textContent = data.prompt_used;
                    
                    // Show LoRA version
                    if (data.lora_version) {
                        const versionText = data.lora_version.toUpperCase();
                        const versionElement = document.getElementById('loraVersionText');
                        versionElement.textContent = versionText;
                        
                        // Different colors for different versions
                        if (data.lora_version === 'v2') {
                            versionElement.style.background = '#ff6b35';
                        } else {
                            versionElement.style.background = '#34c759';
                        }
                    }
                }
            }
            
            // Update background removal step
            if (data.background_processing) {
                setStepStatus('background', 'processing', 'Удаление фона...');
                document.getElementById('step-background').classList.add('active');
            }
            
            if (data.background_completed) {
                setStepStatus('background', 'completed', 'Завершено');
                document.getElementById('step-background').classList.remove('active');
                document.getElementById('step-background').classList.add('completed');
                
                if (data.background_image_url) {
                    document.getElementById('img-background').src = data.background_image_url;
                    document.getElementById('download-background').href = data.background_image_url;
                    document.getElementById('download-background').style.display = 'inline-block';
                }
            }
            
            // Update final step
            if (data.final_processing) {
                setStepStatus('final', 'processing', 'Финализация...');
                document.getElementById('step-final').classList.add('active');
            }
            
            if (data.final_completed) {
                setStepStatus('final', 'completed', 'Готово!');
                document.getElementById('step-final').classList.remove('active');
                document.getElementById('step-final').classList.add('completed');
                
                if (data.final_image_url) {
                    document.getElementById('img-final').src = data.final_image_url;
                    document.getElementById('download-final').href = data.final_image_url;
                    document.getElementById('download-final').style.display = 'inline-block';
                }
            }
            
            // Handle errors
            if (data.error) {
                const currentStep = data.current_step || 'analysis';
                setStepStatus(currentStep, 'error', `Ошибка: ${data.error}`);
                document.getElementById(`step-${currentStep}`).classList.add('error');
                document.getElementById(`step-${currentStep}`).classList.remove('active');
            }
        }
        
        function setStepStatus(step, status, text) {
            const statusEl = document.getElementById(`status-${step}`);
            statusEl.className = `step-status status-${status}`;
            statusEl.textContent = text;
        }
    </script>
</body>
</html>
'''

# History template for batch history
HISTORY_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>История обработки</title>
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
            font-weight: 500;
        }
        .back-link:hover { color: #0056b3; }
        table {
            width: 100%;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        th, td {
            padding: 16px 12px;
            text-align: left;
            border-bottom: 1px solid #e5e5e5;
        }
        th {
            background: #f5f5f7;
            font-weight: 600;
            color: #1d1d1f;
        }
        .status-completed { color: #34c759; }
        .status-processing { color: #007aff; }
        .status-error { color: #ff3b30; }
        .download-btn {
            display: inline-block;
            padding: 8px 16px;
            background: #34c759;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
        }
        .download-btn:hover { background: #30b350; }
        .download-btn:disabled,
        .download-btn.disabled {
            background: #ccc;
            color: #666;
            cursor: not-allowed;
        }
        .stats {
            font-size: 14px;
            color: #666;
        }
        .batch-id {
            font-family: monospace;
            font-size: 12px;
            color: #666;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #86868b;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Вернуться к обработке</a>
        <h1>История обработки</h1>
        {% if history %}
        <table>
            <thead>
                <tr>
                    <th>Batch ID</th>
                    <th>Дата создания</th>
                    <th>Файлов</th>
                    <th>Успешно / Ошибок</th>
                    <th>Время обработки</th>
                    <th>Статус</th>
                    <th>Скачать</th>
                </tr>
            </thead>
            <tbody>
                {% for batch in history %}
                <tr>
                    <td class="batch-id">{{ batch.batch_id }}</td>
                    <td>{{ batch.created_at[:16].replace('T', ' ') if batch.created_at else '-' }}</td>
                    <td>{{ batch.total_files }}</td>
                    <td class="stats">
                        <span style="color: #34c759;">{{ batch.successful or 0 }}</span> / 
                        <span style="color: #ff3b30;">{{ batch.failed or 0 }}</span>
                    </td>
                    <td>{{ '%.1f' % batch.processing_time if batch.processing_time else '-' }}с</td>
                    <td class="status-{{ batch.status or 'unknown' }}">
                        {% if batch.status == 'completed' %}
                            Завершено
                        {% elif batch.status == 'processing' %}
                            Обработка
                        {% else %}
                            {{ batch.status }}
                        {% endif %}
                    </td>
                    <td>
                        {% if batch.zip_path and batch.status == 'completed' %}
                            <a href="/download/{{ batch.batch_id }}" class="download-btn">
                                Скачать ZIP
                            </a>
                        {% else %}
                            <span class="download-btn disabled">Недоступно</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state">
            <h3>Нет данных об обработке</h3>
            <p>Когда вы обработаете изображения, результаты появятся здесь.</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/process_single', methods=['POST'])
def process_single():
    """Process single image with detailed steps"""
    try:
        file = request.files.get('file')
        enhance = request.form.get('enhance') == 'true'
        debug = request.form.get('debug') == 'true'
        custom_prompt = request.form.get('customPrompt') == 'true'
        custom_prompt_text = request.form.get('customPromptText', '').strip()
        lora_version = request.form.get('loraVersion', 'v1')
        
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        # Generate processing ID
        processing_id = f"single_{int(time.time())}"
        single_progress_data[processing_id] = {
            'processing_id': processing_id,
            'current_step': 'analysis',
            'analysis_completed': False,
            'background_processing': False,
            'background_completed': False,
            'final_processing': False,
            'final_completed': False,
            'completed': False,
            'error': None
        }
        
        # Read file content
        file_content = file.stream.read()
        file_data = {
            'filename': file.filename,
            'content': file_content,
            'content_type': file.content_type
        }
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_single_background,
            args=(file_data, processing_id, enhance, debug, custom_prompt, custom_prompt_text, lora_version)
        )
        thread.start()
        
        return jsonify({'processing_id': processing_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/single_progress/<processing_id>')
def get_single_progress(processing_id):
    """Get single processing progress"""
    if processing_id in single_progress_data:
        return jsonify(single_progress_data[processing_id])
    return jsonify({'error': 'Processing not found'}), 404

@app.route('/single_image/<processing_id>/<step>')
def get_single_image(processing_id, step):
    """Get processed image from specific step"""
    if processing_id not in single_progress_data:
        return "Processing not found", 404
    
    # Image paths for different steps
    image_path = f"processed/single_{processing_id}/{step}.png"
    
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/png')
    
    return "Image not found", 404

def process_single_background(file_data, processing_id, enhance, debug, custom_prompt, custom_prompt_text, lora_version='v1'):
    """Background processing for single image"""
    try:
        # Create processing directory
        process_dir = Path(f"processed/single_{processing_id}")
        process_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file wrapper
        file_wrapper = FileDataWrapper(file_data)
        
        # Set debug mode
        batch_processor.positioner.set_debug_mode(debug)
        
        # Step 1: Save original
        original_path = process_dir / "original.png"
        image = Image.open(file_wrapper.stream).convert('RGBA')
        image.save(original_path, 'PNG')
        
        # Step 2: GPT Analysis
        single_progress_data[processing_id]['current_step'] = 'analysis'
        analysis = batch_processor.gpt_analyzer.analyze_image(image)
        single_progress_data[processing_id]['analysis_data'] = analysis
        single_progress_data[processing_id]['analysis_completed'] = True
        
        # Determine prompt to use
        if custom_prompt and custom_prompt_text:
            prompt_to_use = custom_prompt_text
        elif custom_prompt and not custom_prompt_text:
            prompt_to_use = "Clean product photo: keep only the main item and its natural shadow on pure #FFFFFF background; remove any extra elements (text, frames, logos, graphics); keep original resolution, no upscaling."
        else:
            prompt_to_use = batch_processor.gpt_analyzer.create_lora_prompt(analysis)
        
        single_progress_data[processing_id]['prompt_used'] = prompt_to_use
        single_progress_data[processing_id]['lora_version'] = lora_version
        
        # Step 3: Background removal
        single_progress_data[processing_id]['current_step'] = 'background'
        single_progress_data[processing_id]['background_processing'] = True
        
        no_bg_image = batch_processor._remove_background_fal_v2(image, prompt_to_use, lora_version)
        if no_bg_image:
            no_bg_path = process_dir / "background.png"
            no_bg_image.save(no_bg_path, 'PNG')
            single_progress_data[processing_id]['background_image_url'] = f"/single_image/{processing_id}/background"
        else:
            raise Exception("Background removal failed")
            
        single_progress_data[processing_id]['background_processing'] = False
        single_progress_data[processing_id]['background_completed'] = True
        
        # Step 4: Smart positioning (if enhance is enabled)
        single_progress_data[processing_id]['current_step'] = 'final'
        single_progress_data[processing_id]['final_processing'] = True
        
        if enhance:
            # Apply smart positioning
            canvas_settings = analysis.get('canvas_settings', {})
            size = canvas_settings.get('size', '1600x1600')
            positioning = canvas_settings.get('positioning', 'centered')
            
            width, height = map(int, size.split('x'))
            final_image = batch_processor.positioner.position_on_canvas(
                no_bg_image, 
                (width, height), 
                positioning
            )
        else:
            final_image = no_bg_image
        
        # Save final image
        final_path = process_dir / "final.png"
        final_image.save(final_path, 'PNG')
        single_progress_data[processing_id]['final_image_url'] = f"/single_image/{processing_id}/final"
        
        single_progress_data[processing_id]['final_processing'] = False
        single_progress_data[processing_id]['final_completed'] = True
        single_progress_data[processing_id]['completed'] = True
        
    except Exception as e:
        print(f"Error in single processing: {e}")
        single_progress_data[processing_id]['error'] = str(e)
        single_progress_data[processing_id]['completed'] = True

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