#!/bin/bash
"""
StockAnalyzer GPU Monitoring Helper
==================================
Easy access to all GPU monitoring tools
"""

echo "🚀 StockAnalyzer GPU Monitoring Tools"
echo "====================================="
echo ""

# Check if we're in the right directory
if [ ! -f "check_gpu_usage.sh" ]; then
    echo "❌ Please run this from the StockAnalyzer directory"
    exit 1
fi

echo "Choose a monitoring option:"
echo ""
echo "1) 📊 Quick GPU Status Check"
echo "2) 🔄 Real-time GPU Monitor (live updates)"
echo "3) 📝 Performance Logger (save to file)"
echo "4) 🖥️  NVIDIA System Info"
echo "5) 📈 Show Recent GPU Logs (if any)"
echo "6) 🧹 Clean Old Log Files"
echo "7) ❓ Help & Tips"
echo ""
echo "0) Exit"
echo ""

read -p "Enter your choice (0-7): " choice

case $choice in
    1)
        echo ""
        echo "🔍 Running Quick GPU Status Check..."
        echo "==================================="
        ./check_gpu_usage.sh
        ;;
    2)
        echo ""
        echo "🔄 Starting Real-time GPU Monitor..."
        echo "Press Ctrl+C to stop monitoring"
        echo "==================================="
        ./monitor_gpu_usage.sh
        ;;
    3)
        echo ""
        read -p "⏱️  Monitoring duration in minutes (default 30): " duration
        duration=${duration:-30}
        
        read -p "📝 Log file name (default gpu_performance.log): " logfile
        logfile=${logfile:-gpu_performance.log}
        
        echo ""
        echo "📝 Starting Performance Logger..."
        echo "Duration: ${duration} minutes"
        echo "Log file: ${logfile}"
        echo "================================="
        python3 gpu_performance_logger.py -t $duration -f $logfile
        ;;
    4)
        echo ""
        echo "🖥️  NVIDIA System Information..."
        echo "==============================="
        nvidia-smi
        ;;
    5)
        echo ""
        echo "📈 Recent GPU Performance Logs..."
        echo "==============================="
        if ls gpu_performance*.log 1> /dev/null 2>&1; then
            echo "Available log files:"
            ls -la gpu_performance*.log
            echo ""
            echo "Latest entries from most recent log:"
            latest_log=$(ls -t gpu_performance*.log | head -1)
            echo "File: $latest_log"
            echo ""
            tail -10 "$latest_log"
        else
            echo "No GPU performance logs found."
            echo "Run option 3 to create performance logs."
        fi
        ;;
    6)
        echo ""
        echo "🧹 Cleaning Old Log Files..."
        echo "==========================="
        if ls gpu_performance*.log 1> /dev/null 2>&1; then
            echo "Found log files:"
            ls -la gpu_performance*.log
            echo ""
            read -p "Delete all GPU performance logs? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                rm gpu_performance*.log
                echo "✅ Log files deleted."
            else
                echo "ℹ️  Log files kept."
            fi
        else
            echo "No log files to clean."
        fi
        ;;
    7)
        echo ""
        echo "❓ GPU Monitoring Help & Tips"
        echo "============================="
        echo ""
        echo "🎯 What the numbers mean:"
        echo "• GPU Utilization 0-5%:    Idle/minimal processing"
        echo "• GPU Utilization 10-30%:  Light AI processing (OCR)"
        echo "• GPU Utilization 30-80%:  Active LLM text generation"
        echo "• GPU Utilization 80-100%: Heavy processing/training"
        echo ""
        echo "• GPU Memory < 1GB:        No AI models loaded"
        echo "• GPU Memory 1-2GB:        Small models or inactive"
        echo "• GPU Memory 2-4GB:        Large models active (Ollama)"
        echo ""
        echo "🔍 Interpreting results:"
        echo "• Look for 'ollama' in GPU processes"
        echo "• High memory usage = model loaded and ready"
        echo "• High utilization = actively generating text"
        echo "• Temperature should stay below 80°C"
        echo ""
        echo "🚀 Optimization tips:"
        echo "• Keep GPU temperature below 75°C for best performance"
        echo "• High memory usage is normal when Ollama is loaded"
        echo "• 100% utilization during processing is excellent"
        echo "• If GPU is idle, check if StockAnalyzer is processing PDFs"
        echo ""
        echo "🐛 Troubleshooting:"
        echo "• No GPU usage: Check if CUDA environment is loaded"
        echo "• Low usage: Verify Ollama is using GPU (not CPU)"
        echo "• High temperature: Check cooling/reduce processing"
        echo ""
        ;;
    0)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please select 0-7."
        exit 1
        ;;
esac

echo ""
echo "📊 Monitoring complete! Run './gpu_monitor.sh' again for more options."
