#!/usr/bin/env python3
"""
GPU Test Script for StockAnalyzer
=================================
Tests CUDA availability and GPU performance.
"""

import torch
import sys

def test_cuda():
    print("PyTorch CUDA Test")
    print("================")
    
    # Check if CUDA is available
    print(f"CUDA Available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            gpu = torch.cuda.get_device_properties(i)
            print(f"\nGPU {i}: {gpu.name}")
            print(f"  Compute Capability: {gpu.major}.{gpu.minor}")
            print(f"  Total Memory: {gpu.total_memory / 1024**3:.1f} GB")
            print(f"  Multiprocessors: {gpu.multi_processor_count}")
        
        # Test tensor operations on GPU
        print("\nTesting GPU operations...")
        device = torch.device('cuda:0')
        
        # Create test tensors
        x = torch.randn(1000, 1000, device=device)
        y = torch.randn(1000, 1000, device=device)
        
        # Measure performance
        import time
        start_time = time.time()
        
        for _ in range(100):
            z = torch.matmul(x, y)
        
        gpu_time = time.time() - start_time
        print(f"GPU Matrix Multiplication (100 iterations): {gpu_time:.3f} seconds")
        
        # Test CPU performance for comparison
        x_cpu = x.cpu()
        y_cpu = y.cpu()
        
        start_time = time.time()
        
        for _ in range(100):
            z_cpu = torch.matmul(x_cpu, y_cpu)
        
        cpu_time = time.time() - start_time
        print(f"CPU Matrix Multiplication (100 iterations): {cpu_time:.3f} seconds")
        print(f"GPU Speedup: {cpu_time/gpu_time:.1f}x")
        
    else:
        print("CUDA not available. Using CPU only.")
        print("Please check:")
        print("1. NVIDIA drivers are installed")
        print("2. System has been rebooted")
        print("3. CUDA toolkit is properly installed")
        return False
    
    return True

def test_ollama_cuda():
    """Test if Ollama can use CUDA"""
    print("\nOllama CUDA Test")
    print("===============")
    
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Ollama is available")
            
            # Check if GPU acceleration is being used
            print("To enable GPU acceleration in Ollama:")
            print("1. Make sure CUDA_VISIBLE_DEVICES=0 is set")
            print("2. Restart Ollama service if running")
            print("3. Check ollama logs for GPU detection")
            
        else:
            print("Ollama not found or not running")
            
    except Exception as e:
        print(f"Error testing Ollama: {e}")

if __name__ == "__main__":
    if test_cuda():
        test_ollama_cuda()
        print("\n✅ GPU setup test completed successfully!")
        print("Your GTX 1650 Ti should now be available for AI workloads.")
    else:
        print("\n❌ GPU setup needs attention.")
        print("Please reboot and run this test again.")
        sys.exit(1)
