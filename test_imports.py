#!/usr/bin/env python3
"""
Test script to verify that the configuration loading works correctly
"""

import sys
import os

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

def test_imports():
    """Test that all imports work correctly"""
    try:
        print("Testing config import...")
        from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
        print(f"✓ Config loaded successfully:")
        print(f"  OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")
        print(f"  OLLAMA_MODEL: {OLLAMA_MODEL}")
        print(f"  OLLAMA_TIMEOUT: {OLLAMA_TIMEOUT}")
        print()
        
        print("Testing transformer_img import...")
        sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
        from transformer_img import OLLAMA_BASE_URL as transformer_url
        print(f"✓ transformer_img loaded successfully")
        print(f"  OLLAMA_BASE_URL: {transformer_url}")
        print()
        
        print("Testing toCsv import...")
        sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))
        from toCsv import OLLAMA_BASE_URL as tocsv_url
        print(f"✓ toCsv loaded successfully")
        print(f"  OLLAMA_BASE_URL: {tocsv_url}")
        print()
        
        print("Testing fastapi import...")
        from server.fastapi import app
        print(f"✓ FastAPI app loaded successfully")
        print()
        
        print("🎉 All imports successful! Server should start without issues.")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()
