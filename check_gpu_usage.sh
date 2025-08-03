#!/bin/bash
"""
Quick GPU Usage Check for StockAnalyzer
=======================================
Simple script to verify if GPU is being used by StockAnalyzer
"""

echo "🔍 StockAnalyzer GPU Usage Check"
echo "================================="
echo ""

# Check if NVIDIA GPU is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ nvidia-smi not found. GPU monitoring not available."
    echo "   Please ensure NVIDIA drivers are installed."
    exit 1
fi

echo "📊 Current GPU Status:"
echo "====================="
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv

echo ""
echo "🔥 GPU Processes (looking for Ollama/Python):"
echo "=============================================="
gpu_processes=$(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv)
if [ -n "$gpu_processes" ]; then
    echo "$gpu_processes"
else
    echo "No active GPU processes found"
fi

echo ""
echo "🚀 Quick Assessment:"
echo "==================="

# Get current stats
GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | tr -d ' ')
MEM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' ')
MEM_TOTAL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | tr -d ' ')
PROCESSES=$(nvidia-smi --query-compute-apps=process_name --format=csv,noheader 2>/dev/null | wc -l)

# Calculate memory percentage
if [ "$MEM_TOTAL" -gt "0" ]; then
    MEM_PERCENT=$(echo "$MEM_USED $MEM_TOTAL" | awk '{print int($1*100/$2)}')
else
    MEM_PERCENT=0
fi

echo "GPU Utilization: ${GPU_UTIL}%"
echo "GPU Memory: ${MEM_USED}MB / ${MEM_TOTAL}MB (${MEM_PERCENT}%)"
echo "Active Processes: $PROCESSES"

echo ""
echo "📋 Status Summary:"
echo "=================="

# Determine overall status
if [ "$GPU_UTIL" -gt "15" ] && [ "$MEM_USED" -gt "2000" ]; then
    echo "✅ EXCELLENT: GPU IS ACTIVELY PROCESSING AI WORKLOADS"
    echo "   → GPU utilization: ${GPU_UTIL}% (High)"
    echo "   → Memory usage: ${MEM_USED}MB (Ollama model loaded)"
    echo "   → StockAnalyzer is using GPU acceleration! 🚀"
elif [ "$GPU_UTIL" -gt "5" ] || [ "$MEM_USED" -gt "1000" ]; then
    echo "💛 GOOD: GPU IS BEING USED"
    echo "   → GPU utilization: ${GPU_UTIL}%"
    echo "   → Memory usage: ${MEM_USED}MB"
    echo "   → Some GPU processing detected"
elif [ "$PROCESSES" -gt "0" ]; then
    echo "⚠️  PARTIAL: GPU PROCESSES DETECTED BUT LOW USAGE"
    echo "   → GPU utilization: ${GPU_UTIL}%"
    echo "   → Memory usage: ${MEM_USED}MB"
    echo "   → Check if StockAnalyzer is actively processing"
else
    echo "❌ IDLE: GPU NOT CURRENTLY BEING USED"
    echo "   → GPU utilization: ${GPU_UTIL}%"
    echo "   → Memory usage: ${MEM_USED}MB"
    echo "   → No active GPU processes"
fi

echo ""
echo "🔍 Ollama Process Check:"
echo "======================="
if pgrep -f "ollama" > /dev/null; then
    echo "✅ Ollama process is running"
    ollama_gpu=$(nvidia-smi --query-compute-apps=process_name,used_memory --format=csv,noheader | grep -i ollama)
    if [ -n "$ollama_gpu" ]; then
        echo "✅ Ollama is using GPU: $ollama_gpu"
    else
        echo "⚠️  Ollama running but not using GPU"
    fi
else
    echo "❌ Ollama process not found"
fi

echo ""
echo "💡 Monitoring Options:"
echo "====================="
echo "• Real-time monitoring: ./monitor_gpu_usage.sh"
echo "• Continuous logging: python3 gpu_performance_logger.py"
echo "• NVIDIA system info: nvidia-smi"
echo ""
echo "🎯 Expected Values for Active Processing:"
echo "• GPU Utilization: 20-80%"
echo "• GPU Memory: 2000-4000MB"
echo "• Active Processes: 1+ (ollama)"
