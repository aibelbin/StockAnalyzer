#!/bin/bash
# NVIDIA GPU Priority Configuration

# Set NVIDIA as primary GPU
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export CUDA_VISIBLE_DEVICES=0

# Start the StockAnalyzer with GPU acceleration
echo "Starting StockAnalyzer with NVIDIA GPU acceleration..."
source venv/bin/activate
python3 run_persistent_server.py
