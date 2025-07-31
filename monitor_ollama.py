#!/usr/bin/env python3
"""
Ollama Performance Monitor for StockAnalyzer
Monitors Ollama performance and system resource usage
"""

import json
import time
import psutil
import requests
from datetime import datetime

def check_ollama_status():
    """Check if Ollama is running and responsive"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running with {len(models)} models loaded")
            for model in models:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0) / (1024**3)  # Convert to GB
                modified = model.get('modified_at', 'Unknown')
                print(f"   📦 {name} ({size:.1f}GB) - Last used: {modified}")
            return True
        else:
            print("❌ Ollama is not responding")
            return False
    except Exception as e:
        print(f"❌ Ollama connection error: {e}")
        return False

def test_ollama_performance():
    """Test Ollama performance with the configured model"""
    try:
        start_time = time.time()
        
        response = requests.post("http://localhost:11434/api/generate", 
            json={
                "model": "llama3:8b",
                "prompt": "Test performance with 8 cores",
                "stream": False,
                "options": {
                    "num_thread": 8,
                    "temperature": 0.1,
                    "num_predict": 20
                }
            },
            timeout=30
        )
        
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get('response', '')
            duration = end_time - start_time
            
            # Extract performance metrics
            total_duration = result.get('total_duration', 0) / 1e9  # Convert to seconds
            load_duration = result.get('load_duration', 0) / 1e9
            prompt_eval_duration = result.get('prompt_eval_duration', 0) / 1e9
            eval_duration = result.get('eval_duration', 0) / 1e9
            
            prompt_eval_count = result.get('prompt_eval_count', 0)
            eval_count = result.get('eval_count', 0)
            
            print(f"\n🚀 Performance Test Results:")
            print(f"   Total time: {duration:.2f}s")
            print(f"   Model load time: {load_duration:.2f}s")
            print(f"   Prompt processing: {prompt_eval_duration:.2f}s ({prompt_eval_count} tokens)")
            print(f"   Text generation: {eval_duration:.2f}s ({eval_count} tokens)")
            
            if eval_duration > 0 and eval_count > 0:
                tokens_per_second = eval_count / eval_duration
                print(f"   🎯 Generation speed: {tokens_per_second:.1f} tokens/second")
            
            print(f"   Generated text: '{generated_text.strip()}'")
            return True
        else:
            print(f"❌ Performance test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Performance test error: {e}")
        return False

def check_system_resources():
    """Check system CPU and memory usage"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    print(f"\n💻 System Resources:")
    print(f"   CPU Usage: {cpu_percent:.1f}%")
    print(f"   Memory Usage: {memory.percent:.1f}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)")
    print(f"   Available Memory: {memory.available / (1024**3):.1f}GB")
    
    # Check CPU cores
    cpu_count = psutil.cpu_count(logical=False)
    logical_cpu_count = psutil.cpu_count(logical=True)
    print(f"   CPU Cores: {cpu_count} physical, {logical_cpu_count} logical")
    
    # Check per-core usage
    cpu_per_core = psutil.cpu_percent(percpu=True, interval=1)
    print(f"   Per-core usage: {', '.join(f'{cpu:.1f}%' for cpu in cpu_per_core)}")

def main():
    print("=" * 50)
    print("StockAnalyzer - Ollama Performance Monitor")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check Ollama status
    ollama_running = check_ollama_status()
    
    # Check system resources
    check_system_resources()
    
    # Test performance if Ollama is running
    if ollama_running:
        test_ollama_performance()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
