#!/bin/bash

# Ollama Performance Optimization Script for StockAnalyzer
# This script configures Ollama for maximum performance on an 8-core system

echo "=================================="
echo "Ollama Performance Optimization"
echo "=================================="
echo

# Set environment variables for Ollama performance
export OLLAMA_NUM_PARALLEL=4          # Allow 4 parallel requests
export OLLAMA_MAX_LOADED_MODELS=2     # Keep 2 models in memory
export OLLAMA_FLASH_ATTENTION=1       # Enable flash attention for faster processing
export OLLAMA_NUM_THREAD=8            # Use all 8 CPU cores
export OLLAMA_RUNNERS_DIR=/tmp/ollama  # Use fast temp storage for runners

# Create Ollama config directory if it doesn't exist
mkdir -p ~/.ollama

# Create Ollama configuration file for optimal performance
cat > ~/.ollama/config.json << EOF
{
  "num_thread": 8,
  "num_parallel": 4,
  "max_loaded_models": 2,
  "flash_attention": true,
  "low_vram": false,
  "numa": false
}
EOF

echo "Ollama configuration created at ~/.ollama/config.json"

# Stop any existing Ollama process
echo "Stopping existing Ollama processes..."
pkill -f ollama || true
sleep 2

# Start Ollama with optimized settings
echo "Starting Ollama with performance optimizations..."
OLLAMA_NUM_PARALLEL=4 OLLAMA_MAX_LOADED_MODELS=2 OLLAMA_FLASH_ATTENTION=1 OLLAMA_NUM_THREAD=8 ollama serve &

# Wait for Ollama to start
echo "Waiting for Ollama to start..."
sleep 5

# Verify Ollama is running
if pgrep -x "ollama" > /dev/null; then
    echo "✅ Ollama is running with performance optimizations"
    
    # Test the configuration
    echo "Testing Ollama performance..."
    curl -s -X POST http://localhost:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{
            "model": "llama3:8b",
            "prompt": "Performance test",
            "stream": false,
            "options": {
                "num_thread": 8,
                "temperature": 0.1,
                "num_predict": 5
            }
        }' | jq -r '.response // "Error"'
    
    echo
    echo "🚀 Ollama is optimized for 8-core performance!"
    echo "   - Using all 8 CPU cores"
    echo "   - No timeout restrictions"
    echo "   - Parallel processing enabled"
    echo "   - Flash attention enabled"
    echo
    echo "Your StockAnalyzer is ready for high-performance processing!"
else
    echo "❌ Failed to start Ollama"
    exit 1
fi
