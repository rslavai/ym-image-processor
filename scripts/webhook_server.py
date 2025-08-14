#!/usr/bin/env python3
"""
GitHub Webhook Server for Automatic Deployment
Listens for push events and triggers deployment
"""

from flask import Flask, request, jsonify
import hashlib
import hmac
import subprocess
import os
import json
import logging
from datetime import datetime
import threading

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-secret-key-here')
DEPLOY_SCRIPT = '/opt/deploy_ym.sh'
LOG_FILE = '/var/log/webhook_deploy.log'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verify_webhook_signature(payload_body, signature_header):
    """
    Verify that the webhook payload was sent from GitHub
    
    Args:
        payload_body: Raw request body
        signature_header: X-Hub-Signature-256 header value
        
    Returns:
        bool: True if signature is valid
    """
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)

def run_deployment():
    """
    Run the deployment script in a separate thread
    """
    try:
        logger.info("Starting deployment process...")
        
        # Make sure deploy script exists and is executable
        if not os.path.exists(DEPLOY_SCRIPT):
            logger.error(f"Deploy script not found: {DEPLOY_SCRIPT}")
            return
        
        # Run deployment script
        result = subprocess.run(
            ['/bin/bash', DEPLOY_SCRIPT],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("Deployment completed successfully")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"Deployment failed with code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("Deployment timed out after 10 minutes")
    except Exception as e:
        logger.error(f"Deployment error: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'webhook-server',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def github_webhook():
    """
    Handle GitHub webhook events
    """
    # Verify webhook signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_webhook_signature(request.data, signature):
        logger.warning("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse webhook payload
    try:
        payload = request.json
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    
    # Check event type
    event = request.headers.get('X-GitHub-Event')
    logger.info(f"Received GitHub event: {event}")
    
    if event == 'ping':
        logger.info("Webhook ping successful")
        return jsonify({'message': 'Pong!'})
    
    if event != 'push':
        logger.info(f"Ignoring event type: {event}")
        return jsonify({'message': f'Event {event} ignored'})
    
    # Check if it's a push to main branch
    if payload.get('ref') != 'refs/heads/main':
        branch = payload.get('ref', '').replace('refs/heads/', '')
        logger.info(f"Ignoring push to branch: {branch}")
        return jsonify({'message': f'Push to {branch} ignored'})
    
    # Log push details
    pusher = payload.get('pusher', {}).get('name', 'unknown')
    commits = len(payload.get('commits', []))
    logger.info(f"Push to main by {pusher} with {commits} commits")
    
    # Trigger deployment in background
    logger.info("Triggering deployment...")
    deployment_thread = threading.Thread(target=run_deployment)
    deployment_thread.daemon = True
    deployment_thread.start()
    
    return jsonify({
        'message': 'Deployment triggered',
        'pusher': pusher,
        'commits': commits
    })

@app.route('/deploy', methods=['POST'])
def manual_deploy():
    """
    Manual deployment trigger (requires secret key)
    """
    secret = request.headers.get('X-Deploy-Secret')
    if secret != WEBHOOK_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
    
    logger.info("Manual deployment triggered")
    deployment_thread = threading.Thread(target=run_deployment)
    deployment_thread.daemon = True
    deployment_thread.start()
    
    return jsonify({'message': 'Manual deployment triggered'})

if __name__ == '__main__':
    logger.info("Starting webhook server...")
    app.run(host='0.0.0.0', port=9000)