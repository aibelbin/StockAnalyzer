#!/bin/bash

# Exit on error
set -e

echo "=================================="
echo "StockAnalyzer Hybrid Setup Script"
echo "=================================="
echo

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "Ollama installed successfully!"
else
    echo "Ollama is already installed."
fi

# Start Ollama service
echo "Starting Ollama service..."
if pgrep -x "ollama" > /dev/null; then
    echo "Ollama service is already running."
else
    ollama serve &
    echo "Ollama service started."
    sleep 5  # Give it a moment to start
fi

# Pull the Llama 2 model
echo "Pulling Llama 2 model (this may take some time)..."
ollama pull llama2:7b

echo
echo "===================================="
echo "Installation and setup completed!"
echo "===================================="
echo
echo "You can now run the StockAnalyzer with:"
echo "python run_server.py"
echo
echo "To check Ollama status: ollama ps"
echo "To stop Ollama: pkill ollama"
