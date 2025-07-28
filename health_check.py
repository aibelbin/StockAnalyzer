#!/usr/bin/env python3
"""
Health check script for Stock Analyzer system
"""

import requests
import time
import os
import sys
from pathlib import Path

def check_fastapi_server():
    """Check if FastAPI server is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✓ FastAPI server is running")
            return True
        else:
            print(f"✗ FastAPI server returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ FastAPI server is not responding: {e}")
        return False

def check_directories():
    """Check if required directories exist"""
    required_dirs = [
        "./corporate_filings_pdfs",
        "./uploaded_pdfs", 
        "./ocr_processed_final",
        "./webScraper",
        "./server"
    ]
    
    all_good = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
            all_good = False
    
    return all_good

def check_key_files():
    """Check if key script files exist"""
    key_files = [
        "./webScraper/nseindia.py",
        "./server/fastapi.py",
        "./server/feeder.py",
        "./server/toCsv.py",
        "./run_server.py"
    ]
    
    all_good = True
    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"✓ File exists: {file_path}")
        else:
            print(f"✗ File missing: {file_path}")
            all_good = False
    
    return all_good

def check_log_files():
    """Check for recent log files"""
    log_files = [
        "./stockanalyzer.log",
        "./server/feeder.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            # Check if file was modified recently (within last hour)
            mtime = os.path.getmtime(log_file)
            age = time.time() - mtime
            if age < 3600:  # 1 hour
                print(f"✓ Recent log activity: {log_file} (last modified {int(age/60)} minutes ago)")
            else:
                print(f"⚠ Old log file: {log_file} (last modified {int(age/3600)} hours ago)")
        else:
            print(f"ℹ Log file not found: {log_file} (may not have run yet)")

def main():
    print("=" * 60)
    print("STOCK ANALYZER SYSTEM HEALTH CHECK")
    print("=" * 60)
    
    print("\n1. Checking directories...")
    dirs_ok = check_directories()
    
    print("\n2. Checking key files...")
    files_ok = check_key_files()
    
    print("\n3. Checking FastAPI server...")
    server_ok = check_fastapi_server()
    
    print("\n4. Checking log files...")
    check_log_files()
    
    print("\n" + "=" * 60)
    print("HEALTH CHECK SUMMARY")
    print("=" * 60)
    
    if dirs_ok and files_ok:
        print("✓ System structure is correct")
    else:
        print("✗ System structure has issues")
    
    if server_ok:
        print("✓ FastAPI server is operational")
    else:
        print("✗ FastAPI server is not running")
        print("  Try running: python run_server.py")
    
    overall_status = dirs_ok and files_ok and server_ok
    
    if overall_status:
        print("\n🎉 System appears to be healthy!")
    else:
        print("\n⚠️  System has some issues that need attention")
    
    return 0 if overall_status else 1

if __name__ == "__main__":
    sys.exit(main())
