#!/bin/bash
"""
Real-Time GPU Monitor for StockAnalyzer
=======================================
Displays live GPU usage statistics to verify GPU acceleration
"""

echo "🚀 StockAnalyzer GPU Monitor - Press Ctrl+C to stop"
echo "=================================================="
echo ""

# Check if nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ nvidia-smi not found. Please ensure NVIDIA drivers are installed."
    exit 1
fi

# Create a function to display GPU stats
monitor_gpu() {
    while true; do
        clear
        echo "🚀 StockAnalyzer GPU Monitor - $(date)"
        echo "=================================================="
        echo ""
        
        # NVIDIA GPU stats
        echo "📊 NVIDIA GTX 1650 Ti Status:"
        nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw --format=csv,noheader,nounits | while read line; do
            IFS=',' read -r gpu_util mem_util mem_used mem_total temp power <<< "$line"
            
            # Color coding for utilization
            if [ "$gpu_util" -gt "70" ]; then
                gpu_color="🔥"
            elif [ "$gpu_util" -gt "30" ]; then
                gpu_color="🚀"
            elif [ "$gpu_util" -gt "5" ]; then
                gpu_color="💛"
            else
                gpu_color="💤"
            fi
            
            echo "  ${gpu_color} GPU Utilization: ${gpu_util}%"
            echo "  🧠 Memory Utilization: ${mem_util}%"
            echo "  💾 Memory Used: ${mem_used}MB / ${mem_total}MB"
            echo "  🌡️  Temperature: ${temp}°C"
            
            # Only show power if supported
            if [ "$power" != "[Not Supported]" ]; then
                echo "  ⚡ Power Draw: ${power}W"
            fi
        done
        
        echo ""
        echo "🔥 Active GPU Processes:"
        gpu_processes=$(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader)
        if [ -n "$gpu_processes" ]; then
            echo "$gpu_processes" | while read line; do
                if [ ! -z "$line" ]; then
                    echo "  ✅ $line"
                fi
            done
        else
            echo "  💤 No active GPU processes"
        fi
        
        echo ""
        echo "💻 System Comparison:"
        
        # CPU usage
        cpu_usage=$(grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$3+$4+$5)} END {print int(usage)}')
        echo "  🖥️  CPU Overall Usage: ${cpu_usage}%"
        
        # Memory usage
        mem_info=$(free | grep Mem)
        mem_total=$(echo $mem_info | awk '{print $2}')
        mem_used=$(echo $mem_info | awk '{print $3}')
        mem_percent=$(echo "$mem_used $mem_total" | awk '{print int($1*100/$2)}')
        echo "  🧠 System RAM Usage: ${mem_percent}%"
        
        echo ""
        echo "📈 GPU Performance Indicators:"
        
        # Get current GPU memory usage
        current_gpu_mem=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
        current_gpu_util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)
        
        # Performance assessment
        if [ "$current_gpu_util" -gt "20" ] && [ "$current_gpu_mem" -gt "2000" ]; then
            echo "  🚀 EXCELLENT: GPU is actively processing AI workloads"
        elif [ "$current_gpu_util" -gt "5" ] || [ "$current_gpu_mem" -gt "1000" ]; then
            echo "  💛 GOOD: GPU is being used for processing"
        else
            echo "  💤 IDLE: GPU is not currently processing"
        fi
        
        echo ""
        echo "📝 Tips:"
        echo "  • High GPU utilization (>30%) = LLM text generation active"
        echo "  • High memory usage (>2GB) = Ollama model loaded"
        echo "  • Look for 'ollama' process in GPU processes list"
        echo ""
        echo "Press Ctrl+C to stop monitoring..."
        
        sleep 2
    done
}

# Trap Ctrl+C to exit gracefully
trap 'echo -e "\n\n👋 Monitoring stopped. GPU stats saved to last check."; exit 0' INT

# Run the monitor
monitor_gpu
