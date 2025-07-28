#!/usr/bin/env python3
"""
Simplified startup script for Stock Analyzer
This script will start the orchestrator with better error handling and monitoring
"""

import os
import sys
import time
import logging
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")
    
    try:
        import uvicorn
    except ImportError:
        missing_deps.append("uvicorn[standard]")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import aiohttp
    except ImportError:
        missing_deps.append("aiohttp")
    
    try:
        import pdf2image
    except ImportError:
        missing_deps.append("pdf2image")
        
    try:
        import pytesseract
    except ImportError:
        missing_deps.append("pytesseract")
    
    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install them using:")
        print("pip install " + " ".join(missing_deps))
        return False
    
    return True

def setup_environment():
    """Setup the environment and directories"""
    print("Setting up environment...")
    
    # Create necessary directories
    directories = [
        "./corporate_filings_pdfs",
        "./uploaded_pdfs",
        "./ocr_processed_final",
        "./webScraper",
        "./server",
        "./logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directory: {directory}")
    
    return True

def main():
    print("=" * 60)
    print("STOCK ANALYZER STARTUP")
    print("=" * 60)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    if not check_dependencies():
        print("❌ Dependency check failed")
        return 1
    print("✅ All dependencies are available")
    
    # Setup environment
    print("\n2. Setting up environment...")
    if not setup_environment():
        print("❌ Environment setup failed")
        return 1
    print("✅ Environment setup completed")
    
    # Start the orchestrator
    print("\n3. Starting Stock Analyzer Orchestrator...")
    print("This will start all components:")
    print("  - FastAPI server (port 8000)")
    print("  - NSE web scraper")
    print("  - PDF feeder (every 5 minutes)")
    print("  - CSV processor (every 10 minutes)")
    print("\nPress Ctrl+C to stop all components")
    print("=" * 60)
    
    try:
        # Import and run the orchestrator
        from run_server import StockAnalyzerOrchestrator
        orchestrator = StockAnalyzerOrchestrator()
        orchestrator.start()
        
    except ImportError as e:
        print(f"❌ Could not import orchestrator: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n✅ Shutdown completed")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
