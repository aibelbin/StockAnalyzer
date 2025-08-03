#!/usr/bin/env python3
"""
GPU Performance Logger for StockAnalyzer
=======================================
Logs GPU usage statistics while processing PDFs
Records data to CSV file for analysis
"""

import subprocess
import time
import datetime
import os
import sys

def get_gpu_stats():
    """Get current GPU statistics from nvidia-smi"""
    try:
        # Get GPU utilization and other stats
        result = subprocess.run([
            'nvidia-smi', 
            '--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(',')
            if len(parts) >= 6:
                gpu_util = int(parts[0].strip())
                mem_util = int(parts[1].strip())
                mem_used = int(parts[2].strip())
                mem_total = int(parts[3].strip())
                temp = int(parts[4].strip())
                power = parts[5].strip()
                
                # Handle power draw - some cards don't support it
                try:
                    power_val = float(power) if power != '[Not Supported]' else 0.0
                except:
                    power_val = 0.0
                
                return {
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'gpu_utilization': gpu_util,
                    'memory_utilization': mem_util,
                    'memory_used_mb': mem_used,
                    'memory_total_mb': mem_total,
                    'temperature_c': temp,
                    'power_draw_w': power_val
                }
    except Exception as e:
        print(f"Error getting GPU stats: {e}")
    return None

def get_gpu_processes():
    """Get current GPU processes"""
    try:
        result = subprocess.run([
            'nvidia-smi',
            '--query-compute-apps=pid,process_name,used_memory',
            '--format=csv,noheader'
        ], capture_output=True, text=True, timeout=10)
        
        processes = []
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 3:
                        processes.append({
                            'pid': parts[0],
                            'process_name': parts[1],
                            'memory_mb': parts[2].replace(' MiB', '').replace(' MB', '')
                        })
        return processes
    except Exception as e:
        print(f"Error getting GPU processes: {e}")
    return []

def check_stockanalyzer_processes():
    """Check if StockAnalyzer related processes are running"""
    try:
        # Check for Python processes that might be StockAnalyzer
        result = subprocess.run(['pgrep', '-f', 'run_persistent_server.py'], 
                              capture_output=True, text=True)
        persistent_server = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        result = subprocess.run(['pgrep', '-f', 'ollama'], 
                              capture_output=True, text=True)
        ollama_processes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        return {
            'persistent_server': persistent_server,
            'ollama_processes': ollama_processes
        }
    except:
        return {'persistent_server': 0, 'ollama_processes': 0}

def monitor_gpu_performance(duration_minutes=30, log_file='gpu_performance.log'):
    """Monitor GPU performance for specified duration"""
    print(f"🚀 GPU Performance Logger for StockAnalyzer")
    print(f"==========================================")
    print(f"📝 Logging to: {log_file}")
    print(f"⏱️  Duration: {duration_minutes} minutes")
    print(f"📊 Checking every 5 seconds")
    print("")
    
    # Check if nvidia-smi is available
    try:
        subprocess.run(['nvidia-smi', '--version'], capture_output=True, check=True)
    except:
        print("❌ nvidia-smi not found. Please ensure NVIDIA drivers are installed.")
        return
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    # Initialize log file
    try:
        with open(log_file, 'w') as f:
            # Write CSV header
            f.write("timestamp,gpu_util_pct,mem_util_pct,mem_used_mb,mem_total_mb,temp_c,power_w,processes,stockanalyzer_active\n")
    except Exception as e:
        print(f"❌ Error creating log file: {e}")
        return
    
    print("📈 Real-time monitoring (Press Ctrl+C to stop early):")
    print("=" * 80)
    
    sample_count = 0
    high_usage_count = 0
    
    try:
        while time.time() < end_time:
            stats = get_gpu_stats()
            processes = get_gpu_processes()
            stockanalyzer_procs = check_stockanalyzer_processes()
            
            if stats:
                sample_count += 1
                
                # Count high usage samples
                if stats['gpu_utilization'] > 20 or stats['memory_used_mb'] > 2000:
                    high_usage_count += 1
                
                # Display real-time stats
                gpu_status = "🔥" if stats['gpu_utilization'] > 30 else "💛" if stats['gpu_utilization'] > 5 else "💤"
                mem_status = "🧠" if stats['memory_used_mb'] > 2000 else "📊" if stats['memory_used_mb'] > 1000 else "💾"
                
                current_time = datetime.datetime.now().strftime('%H:%M:%S')
                
                print(f"\r{current_time} | "
                      f"{gpu_status} GPU: {stats['gpu_utilization']:3d}% | "
                      f"{mem_status} MEM: {stats['memory_used_mb']:4d}MB/{stats['memory_total_mb']}MB "
                      f"({stats['memory_utilization']:3d}%) | "
                      f"🌡️ {stats['temperature_c']:2d}°C | "
                      f"🔧 Procs: {len(processes)} | "
                      f"📊 SA: {'✅' if stockanalyzer_procs['persistent_server'] > 0 else '❌'}", 
                      end='', flush=True)
                
                # Log to file
                try:
                    with open(log_file, 'a') as f:
                        process_names = [p['process_name'] for p in processes]
                        stockanalyzer_active = stockanalyzer_procs['persistent_server'] > 0 or stockanalyzer_procs['ollama_processes'] > 0
                        
                        f.write(f"{stats['timestamp']},{stats['gpu_utilization']},{stats['memory_utilization']},"
                               f"{stats['memory_used_mb']},{stats['memory_total_mb']},{stats['temperature_c']},"
                               f"{stats['power_draw_w']},\"{';'.join(process_names)}\",{stockanalyzer_active}\n")
                except Exception as e:
                    print(f"\n⚠️ Error writing to log: {e}")
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Monitoring stopped by user after {sample_count} samples.")
    
    # Summary
    print(f"\n\n📊 Monitoring Summary:")
    print(f"=" * 50)
    print(f"📝 Log file: {log_file}")
    print(f"⏱️  Total samples: {sample_count}")
    print(f"🚀 High usage samples: {high_usage_count} ({high_usage_count*100//max(sample_count,1)}%)")
    
    if high_usage_count > sample_count * 0.5:
        print(f"✅ EXCELLENT: GPU was actively used for most of the monitoring period!")
    elif high_usage_count > sample_count * 0.2:
        print(f"💛 GOOD: GPU showed moderate activity during monitoring.")
    else:
        print(f"⚠️ LOW: GPU usage was minimal during monitoring period.")
    
    print(f"\n💡 Tip: Analyze the log file with:")
    print(f"   • Excel/LibreOffice for charts")
    print(f"   • grep 'True' {log_file} | wc -l  # Count active periods")
    print(f"   • sort -t, -k2 -nr {log_file}     # Sort by GPU usage")

def main():
    """Main function with command line argument support"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor GPU performance for StockAnalyzer')
    parser.add_argument('-t', '--time', type=int, default=30, 
                       help='Monitoring duration in minutes (default: 30)')
    parser.add_argument('-f', '--file', type=str, default='gpu_performance.log',
                       help='Log file name (default: gpu_performance.log)')
    
    args = parser.parse_args()
    
    # Validate duration
    if args.time < 1 or args.time > 1440:  # Max 24 hours
        print("❌ Duration must be between 1 and 1440 minutes")
        return
    
    monitor_gpu_performance(args.time, args.file)

if __name__ == "__main__":
    main()
