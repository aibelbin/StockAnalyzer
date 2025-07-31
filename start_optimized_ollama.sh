#!/bin/bash

# Optimized Ollama Startup Script for 8-Core Performance
echo "Starting Ollama with 8-core optimization..."

# Set environment variables for maximum performance
export OLLAMA_NUM_PARALLEL=8          # Allow 8 parallel requests (one per core)
export OLLAMA_MAX_LOADED_MODELS=2     # Keep models in memory
export OLLAMA_FLASH_ATTENTION=1       # Enable flash attention
export OLLAMA_NUM_THREAD=8            # Use all 8 threads
export OLLAMA_RUNNERS_DIR=/tmp/ollama  # Use fast temp storage
export OLLAMA_MAX_QUEUE=16            # Larger queue for requests
export OLLAMA_CONCURRENCY=8           # Max concurrent operations

# Start Ollama with optimized settings
echo "Environment variables set:"
echo "  OLLAMA_NUM_PARALLEL: $OLLAMA_NUM_PARALLEL"
echo "  OLLAMA_NUM_THREAD: $OLLAMA_NUM_THREAD"
echo "  OLLAMA_CONCURRENCY: $OLLAMA_CONCURRENCY"

echo "Starting Ollama server..."
ollama serve &

# Wait for startup
sleep 3

# Verify it's running
if pgrep -x "ollama" > /dev/null; then
    echo "✅ Ollama started successfully with 8-core optimization"
    
    # Show process info
    echo "Ollama processes:"
    ps aux | grep ollama | grep -v grep
    
    echo ""
    echo "🚀 Ollama is now optimized for maximum 8-core performance!"
else
    echo "❌ Failed to start Ollama"
    exit 1
fi
