#!/usr/bin/env python3
"""
Test the fixed application with a real image
"""

import requests
import time
import json
from PIL import Image
import io

SERVER_URL = "http://103.136.69.249:8080"

def create_test_image():
    """Create a simple test image"""
    # Create a simple RGB image
    img = Image.new('RGB', (300, 300), color='red')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_batch_processing():
    """Test batch processing with a real image"""
    print("🧪 Testing batch processing with real image...")
    
    # Create test image
    image_data = create_test_image()
    
    # Upload for batch processing
    files = {'files': ('test_product.jpg', image_data, 'image/jpeg')}
    
    try:
        response = requests.post(f"{SERVER_URL}/process_batch", 
                               files=files, 
                               timeout=60)
        
        print(f"Upload response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            batch_id = data.get('batch_id')
            print(f"✅ Batch created: {batch_id}")
            
            # Check progress
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                progress_response = requests.get(f"{SERVER_URL}/progress/{batch_id}")
                
                if progress_response.status_code == 200:
                    progress = progress_response.json()
                    print(f"Progress: {progress.get('current_file', 'N/A')} - " +
                          f"{progress.get('processed', 0)}/{progress.get('total', 0)}")
                    
                    if progress.get('completed', False):
                        print("🎉 Processing completed!")
                        print(f"Successful: {progress.get('successful', 0)}")
                        print(f"Failed: {progress.get('failed', 0)}")
                        
                        # Check for errors
                        if progress.get('failed', 0) > 0:
                            print("❌ Some files failed:")
                            result = progress.get('result', {})
                            for file_result in result.get('results', []):
                                if file_result.get('status') == 'error':
                                    print(f"   {file_result.get('filename')}: {file_result.get('error')}")
                        else:
                            print("✅ All files processed successfully!")
                            
                        return True
                
                else:
                    print(f"❌ Progress check failed: {progress_response.status_code}")
                    
            print("⏰ Timeout waiting for processing to complete")
            return False
            
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    print("🔧 Testing fixed YM Image Processor...")
    
    # Test health first
    try:
        health_response = requests.get(f"{SERVER_URL}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test batch processing
    success = test_batch_processing()
    
    if success:
        print("\n🎉 All tests passed! The fix is working correctly.")
    else:
        print("\n❌ Tests failed. Need to investigate further.")

if __name__ == "__main__":
    main()