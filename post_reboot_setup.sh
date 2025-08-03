#!/bin/bash

echo "================================================================"
echo "Post-Reboot GPU Verification for StockAnalyzer"
echo "================================================================"

# Check NVIDIA driver status
echo "Checking NVIDIA driver..."
nvidia-smi
if [ $? -eq 0 ]; then
    echo "✅ NVIDIA drivers loaded successfully!"
else
    echo "❌ NVIDIA drivers not detected. Please check installation."
    exit 1
fi

# Activate virtual environment and test GPU
echo -e "\nTesting GPU acceleration..."
cd /home/fox/Documents/StockAnalyzer
source venv/bin/activate

# Test PyTorch CUDA
python3 test_gpu.py
if [ $? -eq 0 ]; then
    echo "✅ GPU acceleration working!"
else
    echo "❌ GPU acceleration failed. Check CUDA installation."
    exit 1
fi

# Configure Ollama for GPU
echo -e "\nConfiguring Ollama for GPU acceleration..."
export OLLAMA_GPU=1
export CUDA_VISIBLE_DEVICES=0

# Start GPU-accelerated services
echo -e "\nStarting GPU-accelerated StockAnalyzer..."
echo "Use: ./nvidia_priority.sh to start with GPU acceleration"
echo "Use: source cuda_config.sh to set environment variables"

echo ""
echo "📊 GPU Monitoring Tools Available:"
echo "• Quick check: ./check_gpu_usage.sh"
echo "• Real-time monitor: ./monitor_gpu_usage.sh"
echo "• Performance logging: python3 gpu_performance_logger.py"
echo "• NVIDIA info: nvidia-smi"

echo "================================================================"
echo "GPU Setup Complete! StockAnalyzer ready for GPU acceleration."
echo "================================================================"
