#!/bin/bash

# Environment setup script for YM Batch Processor
# Run with: source setup_env.sh

echo "Setting up environment variables for YM Batch Processor..."

# OpenAI API Key for GPT-4 Vision
export OPENAI_API_KEY="y1__xDajc-RpdT-ARiuKyDznuMCNDLvZ7L9s40pcN2X-QL3l1X-suw"

# Fal.ai API Key (existing)
export FAL_API_KEY="1b2d09e7-b561-4e66-b5df-c777ec28361f:c22376d251287771501f26cfdabf3ff5"

# LoRA Model Path (existing)
export LORA_PATH="https://v3.fal.media/files/rabbit/McQtMDl9HQ2cKh0_E-CrO_adapter_model.safetensors"

# Port configuration
export PORT=8081

echo "Environment variables set:"
echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
echo "  FAL_API_KEY: ${FAL_API_KEY:0:10}..."
echo "  LORA_PATH: Set"
echo "  PORT: $PORT"
echo ""
echo "Ready to run: python3 app_batch.py"