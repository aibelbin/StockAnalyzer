#!/usr/bin/env python3
"""
Debug script to check configuration loading
"""
import os
import sys

print("=== Environment Variables ===")
for key in os.environ:
    if 'OLLAMA' in key:
        print(f"{key}: {os.environ[key]}")

print("\n=== Testing configuration imports ===")

# Test root config
try:
    from config import OLLAMA_MODEL as ROOT_OLLAMA_MODEL
    print(f"Root config OLLAMA_MODEL: {ROOT_OLLAMA_MODEL}")
except Exception as e:
    print(f"Root config import failed: {e}")

# Test server config
try:
    sys.path.append('server')
    from config import OLLAMA_MODEL as SERVER_OLLAMA_MODEL
    print(f"Server config OLLAMA_MODEL: {SERVER_OLLAMA_MODEL}")
except Exception as e:
    print(f"Server config import failed: {e}")

# Test tools config
try:
    sys.path.append('tools')
    from config import OLLAMA_MODEL as TOOLS_OLLAMA_MODEL
    print(f"Tools config OLLAMA_MODEL: {TOOLS_OLLAMA_MODEL}")
except Exception as e:
    print(f"Tools config import failed: {e}")

print("\n=== .env file contents ===")
env_files = ['.env', 'server/.env', 'tools/.env']
for env_file in env_files:
    if os.path.exists(env_file):
        print(f"\n{env_file}:")
        with open(env_file, 'r') as f:
            print(f.read())
    else:
        print(f"{env_file}: Not found")

print("\n=== Testing transformer_img.py import simulation ===")
os.chdir('tools')
sys.path.insert(0, '..')
try:
    from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
    print(f"transformer_img.py would get OLLAMA_MODEL: {OLLAMA_MODEL}")
except ImportError as e:
    print(f"Config import failed, using environment: {e}")
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral:7b-instruct-v0.3-fp16")
    OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "0"))
    print(f"Environment fallback OLLAMA_MODEL: {OLLAMA_MODEL}")
