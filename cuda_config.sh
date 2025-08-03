#!/bin/bash
# CUDA Environment Configuration for StockAnalyzer

# Set CUDA paths
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Force NVIDIA GPU usage
export CUDA_VISIBLE_DEVICES=0
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia

# PyTorch CUDA settings
export TORCH_CUDA_ARCH_LIST="7.5"  # GTX 1650 Ti architecture
export CUDA_LAUNCH_BLOCKING=0      # For better performance

echo "CUDA environment configured for GTX 1650 Ti"
