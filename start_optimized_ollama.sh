#!/bin/bash

# Optimized Ollama Startup Script for 8-Core Performance
echo "🚀 Starting Ollama with 8-core optimization..."

# Stop any existing Ollama processes
echo "Stopping any existing Ollama processes..."
pkill -f ollama
sleep 2

# Set environment variables for maximum performance
export OLLAMA_NUM_PARALLEL=8          # Allow 8 parallel requests (one per core)
export OLLAMA_MAX_LOADED_MODELS=2     # Keep models in memory
export OLLAMA_FLASH_ATTENTION=1       # Enable flash attention
export OLLAMA_NUM_THREAD=8            # Use all 8 threads
export OLLAMA_RUNNERS_DIR=/tmp/ollama  # Use fast temp storage
export OLLAMA_MAX_QUEUE=16            # Larger queue for requests
export OLLAMA_CONCURRENCY=8           # Max concurrent operations
export OLLAMA_KEEP_ALIVE=300          # Keep models loaded for 5 minutes
export OLLAMA_HOST=0.0.0.0             # Listen on all interfaces
export OLLAMA_ORIGINS=*                # Allow all origins

# Start Ollama with optimized settings
echo "Environment variables set:"
echo "  OLLAMA_NUM_PARALLEL: $OLLAMA_NUM_PARALLEL"
echo "  OLLAMA_NUM_THREAD: $OLLAMA_NUM_THREAD"
echo "  OLLAMA_CONCURRENCY: $OLLAMA_CONCURRENCY"
echo "  OLLAMA_MAX_QUEUE: $OLLAMA_MAX_QUEUE"

echo "Starting Ollama server..."
ollama serve &

# Wait for startup
echo "Waiting for Ollama to start..."
sleep 5

# Verify it's running
if pgrep -x "ollama" > /dev/null; then
    echo "✅ Ollama started successfully with 8-core optimization"
    
    # Show process info
    echo "Ollama processes:"
    ps aux | grep ollama | grep -v grep
    
    # Test the connection
    echo ""
    echo "Testing Ollama connection..."
    curl -s http://localhost:11434/api/tags >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Ollama API is responding"
        
        # Load the model to start using all cores
        echo "Loading llama3:8b model..."
        ollama run llama3:8b "Hi" >/dev/null 2>&1 &
        
        echo ""
        echo "🚀 Ollama is now optimized for maximum 8-core performance!"
        echo "🔥 Model loaded and ready for high-performance processing!"
        
        # Show CPU usage
        echo ""
        echo "Current CPU usage:"
        top -bn1 | grep "Cpu(s)" || echo "CPU info not available"
        
    else
        echo "⚠️  Ollama started but API is not responding yet. Give it a moment."
    fi
    
else
    echo "❌ Failed to start Ollama"
    exit 1
fi
