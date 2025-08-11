"""
Monitoring and logging utilities for YM Image Processor
"""

import logging
import time
import json
import os
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional
import traceback

# Configure logging
def setup_logging(log_level=logging.INFO, log_file='logs/ym_processor.log'):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level
        log_file: Path to log file
    """
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Create logger for this module
    logger = logging.getLogger('ym_processor')
    return logger

# Performance monitoring decorator
def monitor_performance(func):
    """
    Decorator to monitor function performance
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger('ym_processor.performance')
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            
            logger.info(f"{func.__name__} completed in {elapsed_time:.2f}s")
            
            # Log to metrics file for analysis
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'function': func.__name__,
                'duration': elapsed_time,
                'status': 'success'
            }
            log_metrics(metrics)
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed_time:.2f}s: {str(e)}")
            
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'function': func.__name__,
                'duration': elapsed_time,
                'status': 'error',
                'error': str(e)
            }
            log_metrics(metrics)
            
            raise
    
    return wrapper

def log_metrics(metrics: Dict[str, Any]):
    """
    Log metrics to a JSON file for analysis
    
    Args:
        metrics: Dictionary of metrics to log
    """
    metrics_file = 'logs/metrics.jsonl'
    os.makedirs('logs', exist_ok=True)
    
    try:
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')
    except Exception as e:
        logging.error(f"Failed to log metrics: {e}")

class ProcessingMonitor:
    """
    Monitor for tracking batch processing statistics
    """
    
    def __init__(self):
        self.logger = logging.getLogger('ym_processor.monitor')
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_time': 0,
            'gpt_calls': 0,
            'lora_calls': 0,
            'average_time': 0
        }
        self.session_start = time.time()
    
    def log_processing(self, 
                      image_name: str,
                      status: str,
                      processing_time: float,
                      details: Optional[Dict[str, Any]] = None):
        """
        Log individual image processing
        
        Args:
            image_name: Name of the processed image
            status: Processing status (success/failed)
            processing_time: Time taken to process
            details: Additional details
        """
        self.stats['total_processed'] += 1
        self.stats['total_time'] += processing_time
        
        if status == 'success':
            self.stats['successful'] += 1
        else:
            self.stats['failed'] += 1
        
        self.stats['average_time'] = self.stats['total_time'] / self.stats['total_processed']
        
        # Log detailed entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'image': image_name,
            'status': status,
            'processing_time': processing_time,
            'details': details or {}
        }
        
        self.logger.info(f"Processed {image_name}: {status} in {processing_time:.2f}s")
        log_metrics(log_entry)
    
    def log_gpt_call(self, success: bool, response_time: float):
        """
        Log GPT-4 Vision API call
        
        Args:
            success: Whether the call was successful
            response_time: API response time
        """
        self.stats['gpt_calls'] += 1
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'api': 'gpt-4-vision',
            'success': success,
            'response_time': response_time
        }
        
        self.logger.debug(f"GPT-4 Vision call: {'success' if success else 'failed'} in {response_time:.2f}s")
        log_metrics(log_entry)
    
    def log_lora_call(self, success: bool, response_time: float):
        """
        Log LoRA model API call
        
        Args:
            success: Whether the call was successful
            response_time: API response time
        """
        self.stats['lora_calls'] += 1
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'api': 'lora',
            'success': success,
            'response_time': response_time
        }
        
        self.logger.debug(f"LoRA call: {'success' if success else 'failed'} in {response_time:.2f}s")
        log_metrics(log_entry)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get processing summary statistics
        
        Returns:
            Dictionary with summary statistics
        """
        session_duration = time.time() - self.session_start
        
        return {
            'session_duration': session_duration,
            'total_processed': self.stats['total_processed'],
            'successful': self.stats['successful'],
            'failed': self.stats['failed'],
            'success_rate': (self.stats['successful'] / self.stats['total_processed'] * 100) 
                           if self.stats['total_processed'] > 0 else 0,
            'average_processing_time': self.stats['average_time'],
            'total_processing_time': self.stats['total_time'],
            'gpt_calls': self.stats['gpt_calls'],
            'lora_calls': self.stats['lora_calls'],
            'images_per_minute': (self.stats['total_processed'] / session_duration * 60) 
                                if session_duration > 0 else 0
        }
    
    def print_summary(self):
        """
        Print formatted summary to console and logs
        """
        summary = self.get_summary()
        
        summary_text = f"""
        ========================================
        Processing Summary
        ========================================
        Session Duration: {summary['session_duration']:.1f}s
        Total Images: {summary['total_processed']}
        Successful: {summary['successful']}
        Failed: {summary['failed']}
        Success Rate: {summary['success_rate']:.1f}%
        
        Performance Metrics:
        - Average Time: {summary['average_processing_time']:.2f}s per image
        - Total Time: {summary['total_processing_time']:.1f}s
        - Throughput: {summary['images_per_minute']:.1f} images/min
        
        API Calls:
        - GPT-4 Vision: {summary['gpt_calls']}
        - LoRA Model: {summary['lora_calls']}
        ========================================
        """
        
        print(summary_text)
        self.logger.info(summary_text)
        
        # Save summary to file
        with open('logs/processing_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

# Error tracking
class ErrorTracker:
    """
    Track and analyze errors for debugging
    """
    
    def __init__(self):
        self.logger = logging.getLogger('ym_processor.errors')
        self.errors = []
    
    def log_error(self, 
                  error_type: str,
                  error_message: str,
                  context: Optional[Dict[str, Any]] = None):
        """
        Log an error with context
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': error_type,
            'message': error_message,
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self.errors.append(error_entry)
        self.logger.error(f"{error_type}: {error_message}")
        
        # Save to error log file
        with open('logs/errors.jsonl', 'a') as f:
            f.write(json.dumps(error_entry) + '\n')
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get error summary
        
        Returns:
            Dictionary with error statistics
        """
        error_types = {}
        for error in self.errors:
            error_type = error['type']
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        
        return {
            'total_errors': len(self.errors),
            'error_types': error_types,
            'recent_errors': self.errors[-10:]  # Last 10 errors
        }

# Initialize global instances
monitor = ProcessingMonitor()
error_tracker = ErrorTracker()
logger = setup_logging()