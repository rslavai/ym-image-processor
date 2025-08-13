"""
Batch Processing Module
Handles multiple image processing with progress tracking
"""

import os
import io
import json
import time
import zipfile
import sqlite3
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from PIL import Image
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .gpt_analyzer import GPTProductAnalyzer
from .smart_positioning import SmartPositioning


class BatchProcessor:
    """Process multiple images with progress tracking and history"""
    
    def __init__(self, db_path: str = "database/history.db"):
        """
        Initialize batch processor
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.gpt_analyzer = GPTProductAnalyzer()
        self.positioner = SmartPositioning()
        self.fal_api_key = os.environ.get('FAL_API_KEY', '')
        self.lora_path = os.environ.get('LORA_PATH', 
            'https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors')
        
        # Initialize database
        self._init_database()
        
        # Processing state
        self.current_batch_id = None
        self.progress_callback = None
        
    def _init_database(self):
        """Initialize SQLite database for processing history"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- GPT Analysis
                category TEXT,
                product_type TEXT,
                orientation TEXT,
                aspect_ratio REAL,
                gpt_analysis TEXT,  -- Full JSON analysis
                gpt_prompt TEXT,
                
                -- File paths
                original_path TEXT,
                no_bg_path TEXT,
                final_path TEXT,
                
                -- Metrics
                processing_time REAL,
                status TEXT,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def process_batch(self, 
                     files: List[Any],
                     progress_callback: Optional[Callable] = None,
                     max_workers: int = 3) -> Dict[str, Any]:
        """
        Process multiple images in batch
        
        Args:
            files: List of file objects
            progress_callback: Function to call with progress updates
            max_workers: Number of parallel workers
            
        Returns:
            Dict with batch results
        """
        self.current_batch_id = f"batch_{int(time.time())}"
        self.progress_callback = progress_callback
        
        # Create batch directories
        batch_dir = Path(f"processed/{self.current_batch_id}")
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        (batch_dir / "originals").mkdir(exist_ok=True)
        (batch_dir / "no_background").mkdir(exist_ok=True)
        (batch_dir / "final").mkdir(exist_ok=True)
        
        results = []
        total_files = len(files)
        processed = 0
        
        # Process files with thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._process_single_image, file, batch_dir): file
                for file in files
            }
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    processed += 1
                    
                    # Update progress
                    if self.progress_callback:
                        self.progress_callback({
                            'processed': processed,
                            'total': total_files,
                            'current_file': result['filename'],
                            'status': result['status']
                        })
                        
                except Exception as e:
                    print(f"Error processing {file.filename}: {e}")
                    results.append({
                        'filename': file.filename,
                        'status': 'error',
                        'error': str(e)
                    })
                    processed += 1
        
        # Create ZIP archive
        zip_path = self._create_zip_archive(batch_dir, results)
        
        return {
            'batch_id': self.current_batch_id,
            'total_files': total_files,
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'error']),
            'results': results,
            'zip_path': zip_path
        }
    
    def _process_single_image(self, file: Any, batch_dir: Path) -> Dict[str, Any]:
        """
        Process a single image through the full pipeline
        
        Args:
            file: File object
            batch_dir: Directory for saving processed files
            
        Returns:
            Processing result dict
        """
        start_time = time.time()
        filename = file.filename
        
        try:
            # Save original
            original_path = batch_dir / "originals" / filename
            os.makedirs(original_path.parent, exist_ok=True)
            
            # Load image directly from stream  
            image = Image.open(file.stream)
            
            # Save image as-is (keep original format)
            image.save(original_path)
            
            # Convert to RGBA for processing only  
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Step 1: GPT Analysis
            gpt_result = self.gpt_analyzer.analyze_image(image)
            
            if gpt_result['success']:
                analysis = gpt_result['analysis']
            else:
                # Use fallback analysis
                analysis = gpt_result.get('fallback', {})
            
            # Step 2: Generate LoRA prompt
            lora_prompt = self.gpt_analyzer.create_lora_prompt(analysis)
            
            # Step 3: Remove background with LoRA
            no_bg_image = self._remove_background_fal(image, lora_prompt)
            
            if no_bg_image:
                # Save no-background version
                no_bg_path = batch_dir / "no_background" / filename
                no_bg_image.save(no_bg_path)
                
                # Step 4: Smart positioning
                final_image = self.positioner.process_image(no_bg_image, analysis)
                
                # Save final version
                final_path = batch_dir / "final" / filename
                
                # Convert RGBA to RGB for JPEG, or save as PNG
                if final_path.suffix.lower() in ['.jpg', '.jpeg']:
                    # Convert to RGB for JPEG
                    if final_image.mode == 'RGBA':
                        rgb_image = Image.new('RGB', final_image.size, (255, 255, 255))
                        rgb_image.paste(final_image, mask=final_image.split()[-1] if final_image.mode == 'RGBA' else None)
                        rgb_image.save(final_path, 'JPEG')
                    else:
                        final_image.save(final_path)
                else:
                    # Save as PNG to preserve transparency
                    final_path = final_path.with_suffix('.png')
                    final_image.save(final_path, 'PNG')
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Save to database
                self._save_to_database({
                    'batch_id': self.current_batch_id,
                    'filename': filename,
                    'category': analysis.get('category', 'unknown'),
                    'product_type': analysis.get('product_identification', {}).get('type', 'unknown'),
                    'orientation': analysis.get('geometry', {}).get('orientation', 'standard'),
                    'aspect_ratio': analysis.get('geometry', {}).get('aspect_ratio', 1.0),
                    'gpt_analysis': json.dumps(analysis),
                    'gpt_prompt': lora_prompt,
                    'original_path': str(original_path),
                    'no_bg_path': str(no_bg_path),
                    'final_path': str(final_path),
                    'processing_time': processing_time,
                    'status': 'success'
                })
                
                return {
                    'filename': filename,
                    'status': 'success',
                    'processing_time': processing_time,
                    'analysis': analysis,
                    'paths': {
                        'original': str(original_path),
                        'no_bg': str(no_bg_path),
                        'final': str(final_path)
                    }
                }
            else:
                raise Exception("Failed to remove background")
                
        except Exception as e:
            # Print detailed error for debugging
            import traceback
            error_msg = f"Error processing {filename}: {str(e)}"
            print(f"ERROR: {error_msg}", flush=True)
            print(f"TRACEBACK: {traceback.format_exc()}", flush=True)
            
            # Also write to file for debugging
            try:
                with open('/app/debug.log', 'a') as f:
                    f.write(f"ERROR: {error_msg}\n")
                    f.write(f"TRACEBACK: {traceback.format_exc()}\n")
                    f.write("="*50 + "\n")
            except:
                pass
            
            # Save error to database
            self._save_to_database({
                'batch_id': self.current_batch_id,
                'filename': filename,
                'status': 'error',
                'error_message': str(e),
                'processing_time': time.time() - start_time
            })
            
            return {
                'filename': filename,
                'status': 'error',
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _remove_background_fal(self, image: Image.Image, prompt: str) -> Optional[Image.Image]:
        """
        Remove background using Fal.ai API with LoRA model
        
        Args:
            image: Input image
            prompt: Optimized prompt from GPT
            
        Returns:
            Image with removed background or None if failed
        """
        if not self.fal_api_key:
            print("FAL_API_KEY not configured")
            return None
        
        try:
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Prepare API request
            headers = {
                "Authorization": f"Key {self.fal_api_key}",
                "Content-Type": "application/json"
            }
            
            # Use FLUX Kontext with LoRA
            data = {
                "image_url": f"data:image/png;base64,{img_base64}",
                "prompt": prompt,
                "num_inference_steps": 30,
                "guidance_scale": 2.5,
                "output_format": "png",
                "enable_safety_checker": False,
                "loras": [
                    {
                        "path": self.lora_path,
                        "scale": 1.0
                    }
                ],
                "resolution_mode": "match_input"
            }
            
            # Make API call
            response = requests.post(
                "https://fal.run/fal-ai/flux-kontext-lora",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'images' in result and len(result['images']) > 0:
                    img_url = result['images'][0]['url']
                    img_response = requests.get(img_url)
                    result_image = Image.open(io.BytesIO(img_response.content))
                    return result_image
            
            # Fallback to BiRefNet if LoRA fails
            print(f"LoRA failed, trying BiRefNet fallback")
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
            print(f"Error in Fal.ai API: {e}")
            return None
    
    def _save_to_database(self, data: Dict[str, Any]):
        """Save processing record to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO processing_history 
            (batch_id, filename, category, product_type, orientation, 
             aspect_ratio, gpt_analysis, gpt_prompt, original_path, 
             no_bg_path, final_path, processing_time, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('batch_id'),
            data.get('filename'),
            data.get('category'),
            data.get('product_type'),
            data.get('orientation'),
            data.get('aspect_ratio'),
            data.get('gpt_analysis'),
            data.get('gpt_prompt'),
            data.get('original_path'),
            data.get('no_bg_path'),
            data.get('final_path'),
            data.get('processing_time'),
            data.get('status'),
            data.get('error_message')
        ))
        
        conn.commit()
        conn.close()
    
    def _create_zip_archive(self, batch_dir: Path, results: List[Dict]) -> str:
        """
        Create ZIP archive of processed images
        
        Args:
            batch_dir: Directory with processed images
            results: Processing results
            
        Returns:
            Path to ZIP file
        """
        zip_path = batch_dir / f"{self.current_batch_id}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add final images
            for result in results:
                if result['status'] == 'success':
                    final_path = result['paths']['final']
                    if os.path.exists(final_path):
                        arcname = f"final/{os.path.basename(final_path)}"
                        zipf.write(final_path, arcname)
            
            # Add processing report
            report = {
                'batch_id': self.current_batch_id,
                'timestamp': datetime.now().isoformat(),
                'total_files': len(results),
                'successful': len([r for r in results if r['status'] == 'success']),
                'failed': len([r for r in results if r['status'] == 'error']),
                'results': results
            }
            
            report_json = json.dumps(report, indent=2)
            zipf.writestr('processing_report.json', report_json)
        
        return str(zip_path)
    
    def get_history(self, batch_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get processing history from database
        
        Args:
            batch_id: Optional batch ID to filter by
            limit: Maximum number of records
            
        Returns:
            List of processing records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if batch_id:
            cursor.execute('''
                SELECT * FROM processing_history 
                WHERE batch_id = ? 
                ORDER BY upload_time DESC 
                LIMIT ?
            ''', (batch_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM processing_history 
                ORDER BY upload_time DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results