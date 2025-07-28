#!/usr/bin/env python3
"""
Configuration checker for Stock Analyzer system
"""

import requests
import os
import sys

def check_ollama():
    """Check if Ollama is running and has required model"""
    print("Checking Ollama configuration...")
    
    # Default configuration
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3:8b-instruct-q4_K_M")
    
    print(f"Ollama URL: {ollama_url}")
    print(f"Required Model: {ollama_model}")
    
    # Check if Ollama is running
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            print("✓ Ollama server is running")
            
            # Check if required model is available
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            if ollama_model in model_names:
                print(f"✓ Model '{ollama_model}' is available")
                return True
            else:
                print(f"✗ Model '{ollama_model}' is not available")
                print("Available models:")
                for model_name in model_names:
                    print(f"  - {model_name}")
                print(f"\nTo install the required model, run:")
                print(f"ollama pull {ollama_model}")
                return False
        else:
            print(f"✗ Ollama server returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to Ollama server: {e}")
        print("\nMake sure Ollama is running:")
        print("ollama serve")
        return False

def check_tesseract():
    """Check if Tesseract OCR is available"""
    print("\nChecking Tesseract OCR...")
    
    try:
        import pytesseract
        from PIL import Image
        
        # Try to get Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract is available (version: {version})")
        return True
        
    except ImportError:
        print("✗ pytesseract package not installed")
        print("Install with: pip install pytesseract")
        return False
    except Exception as e:
        print(f"✗ Tesseract not properly configured: {e}")
        print("Make sure Tesseract OCR is installed on your system")
        return False

def check_pdf_processing():
    """Check if PDF processing dependencies are available"""
    print("\nChecking PDF processing capabilities...")
    
    try:
        import pdf2image
        print("✓ pdf2image is available")
    except ImportError:
        print("✗ pdf2image not installed")
        print("Install with: pip install pdf2image")
        return False
    
    try:
        from PIL import Image
        print("✓ PIL/Pillow is available")
    except ImportError:
        print("✗ PIL/Pillow not installed")
        print("Install with: pip install pillow")
        return False
    
    return True

def check_web_dependencies():
    """Check web-related dependencies"""
    print("\nChecking web dependencies...")
    
    dependencies = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("requests", "HTTP client"),
        ("aiohttp", "Async HTTP client")
    ]
    
    all_good = True
    for package, description in dependencies:
        try:
            __import__(package)
            print(f"✓ {package} ({description})")
        except ImportError:
            print(f"✗ {package} not installed ({description})")
            all_good = False
    
    if not all_good:
        print("\nInstall missing packages with:")
        print("pip install -r requirements.txt")
    
    return all_good

def main():
    print("=" * 60)
    print("STOCK ANALYZER CONFIGURATION CHECK")
    print("=" * 60)
    
    checks = [
        ("Ollama LLM", check_ollama),
        ("Tesseract OCR", check_tesseract),
        ("PDF Processing", check_pdf_processing),
        ("Web Dependencies", check_web_dependencies)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Error checking {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    
    all_good = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:20} {status}")
        if not result:
            all_good = False
    
    if all_good:
        print("\n🎉 All configurations are correct!")
        print("You can now run: python start.py")
    else:
        print("\n⚠️  Some configurations need attention")
        print("Please fix the issues above before running the system")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
