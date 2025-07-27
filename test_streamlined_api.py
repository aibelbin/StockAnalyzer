#!/usr/bin/env python3
"""
Simple test script for the streamlined FastAPI PDF OCR workflow
"""

import requests
import sys
import os

def test_upload_pdf(pdf_path: str, server_url: str = "http://localhost:8000"):
    """Test uploading a PDF to the streamlined FastAPI server"""
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return False
    
    print(f"Testing streamlined PDF upload workflow...")
    print(f"Server: {server_url}")
    print(f"PDF file: {pdf_path}")
    print("-" * 50)
    
    try:
        # Test server connectivity
        print("Checking server status...")
        response = requests.get(f"{server_url}/")
        if response.status_code == 200:
            info = response.json()
            print(f"Server online: {info.get('message')} v{info.get('version')}")
            print(f"Status: {info.get('status')}")
        else:
            print(f"Server check failed: {response.status_code}")
            return False
        
        print("\nUploading PDF for processing...")
        
        # Upload PDF file
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            response = requests.post(f"{server_url}/upload_pdf", files=files, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('message')}")
            print(f"File ID: {result.get('file_id')}")
            print(f"Original filename: {result.get('original_filename')}")
            print(f"Processed file saved to: {result.get('processed_file_path')}")
            print(f"Quality score: {result.get('quality_score')}")
            print(f"Pages processed: {result.get('pages_processed')}")
            
            stats = result.get('processing_stats', {})
            print(f"Raw text length: {stats.get('raw_text_length'):,} chars")
            print(f"Processed text length: {stats.get('processed_text_length'):,} chars")
            
            return True
        else:
            print(f"Upload failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("Error: Request timed out (processing may still be running on server)")
        return False
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure it's running.")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_streamlined_api.py <pdf_file_path> [server_url]")
        print("Example: python test_streamlined_api.py document.pdf")
        print("Example: python test_streamlined_api.py document.pdf http://localhost:8000")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    server_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    success = test_upload_pdf(pdf_path, server_url)
    sys.exit(0 if success else 1)
