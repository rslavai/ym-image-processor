#!/bin/bash

# Server Deployment Script for YM Image Processor
# This script should be placed on the server at /opt/deploy_ym.sh

set -e  # Exit on error

echo "🚀 Starting YM Image Processor Deployment"
echo "========================================="

# Configuration
PROJECT_DIR="/opt/ym-image-processor"
DOCKER_IMAGE="ym-processor"
CONTAINER_NAME="ym-processor"
PORT="8080"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root or with sudo"
    exit 1
fi

# Step 1: Navigate to project directory
print_status "Navigating to project directory..."
if [ ! -d "$PROJECT_DIR" ]; then
    print_warning "Project directory not found. Cloning repository..."
    cd /opt
    git clone https://github.com/rslavai/ym-image-processor.git
fi
cd "$PROJECT_DIR"

# Step 2: Pull latest changes
print_status "Pulling latest changes from Git..."
git fetch origin
git reset --hard origin/main
git pull origin main

# Step 3: Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << 'EOF'
FAL_API_KEY=1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5
LORA_PATH=https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors
OPENAI_API_KEY=y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw
PORT=8080
EOF
    print_status ".env file created"
else
    print_status ".env file already exists"
fi

# Step 4: Stop existing container
print_status "Stopping existing container..."
docker stop "$CONTAINER_NAME" 2>/dev/null || print_warning "No existing container to stop"
docker rm "$CONTAINER_NAME" 2>/dev/null || print_warning "No existing container to remove"

# Step 5: Remove old image to ensure fresh build
print_status "Removing old Docker image..."
docker rmi "$DOCKER_IMAGE" 2>/dev/null || print_warning "No existing image to remove"

# Step 6: Build new Docker image
print_status "Building new Docker image..."
docker build -t "$DOCKER_IMAGE" .

if [ $? -ne 0 ]; then
    print_error "Docker build failed!"
    exit 1
fi

# Step 7: Run new container
print_status "Starting new container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart always \
    -p "${PORT}:${PORT}" \
    --env-file .env \
    -v "${PROJECT_DIR}/database:/app/database" \
    -v "${PROJECT_DIR}/processed:/app/processed" \
    -v "${PROJECT_DIR}/uploads:/app/uploads" \
    "$DOCKER_IMAGE"

if [ $? -ne 0 ]; then
    print_error "Failed to start container!"
    exit 1
fi

# Step 8: Wait for container to be ready
print_status "Waiting for container to be ready..."
sleep 5

# Step 9: Check container status
if docker ps | grep -q "$CONTAINER_NAME"; then
    print_status "Container is running"
    
    # Show last 20 lines of logs
    echo ""
    echo "📋 Container logs:"
    echo "=================="
    docker logs --tail 20 "$CONTAINER_NAME"
    
    # Test health endpoint
    echo ""
    echo "🔍 Testing health endpoint..."
    HEALTH_CHECK=$(curl -s http://localhost:${PORT}/health || echo "Failed")
    
    if echo "$HEALTH_CHECK" | grep -q "healthy"; then
        print_status "Health check passed!"
        echo "$HEALTH_CHECK" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_CHECK"
    else
        print_warning "Health check failed or service still starting"
    fi
    
    echo ""
    echo "========================================="
    print_status "Deployment completed successfully!"
    echo ""
    echo "🌐 Service available at:"
    echo "   Internal: http://localhost:${PORT}"
    echo "   External: http://$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP"):${PORT}"
    echo ""
    echo "📊 Useful commands:"
    echo "   View logs:    docker logs -f $CONTAINER_NAME"
    echo "   Restart:      docker restart $CONTAINER_NAME"
    echo "   Stop:         docker stop $CONTAINER_NAME"
    echo "   Stats:        docker stats $CONTAINER_NAME"
    
else
    print_error "Container failed to start!"
    echo ""
    echo "📋 Error logs:"
    docker logs "$CONTAINER_NAME"
    exit 1
fi

# Step 10: Clean up old Docker images
print_status "Cleaning up unused Docker images..."
docker image prune -f

echo ""
echo "✨ All done!"