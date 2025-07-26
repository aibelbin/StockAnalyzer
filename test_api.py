#!/usr/bin/env python3
"""
Test script for the PDF OCR API
"""

import requests
import json
import time
import os

# API base URL
BASE_URL = "http://localhost:8000"

def test_api():
    """Test the PDF OCR API endpoints"""
    
    print("Testing Stock Analyzer PDF OCR API")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ Server is running: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running. Please start the server first.")
        return
    
    # Test 2: Check acquired PDFs endpoint
    response = requests.get(f"{BASE_URL}/acquired_pdfs")
    print(f"📋 Current processing status: {len(response.json().get('processing_status', {}))} files")
    
    # Test 3: Upload a PDF (if one exists)
    test_pdf_path = None
    
    # Look for PDF files in common locations
    possible_paths = [
        "160301289-Warren-Buffett-Katharine-Graham-Letter.pdf",
        "../160301289-Warren-Buffett-Katharine-Graham-Letter.pdf",
        "test.pdf",
        "sample.pdf"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            test_pdf_path = path
            break
    
    if test_pdf_path:
        print(f"📤 Uploading test PDF: {test_pdf_path}")
        
        with open(test_pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(test_pdf_path), f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/upload_pdf", files=files)
        
        if response.status_code == 200:
            result = response.json()
            file_id = result['file_id']
            print(f"✓ PDF uploaded successfully. File ID: {file_id}")
            
            # Test 4: Monitor processing status
            print("⏳ Monitoring processing status...")
            while True:
                status_response = requests.get(f"{BASE_URL}/status/{file_id}")
                status_data = status_response.json()
                print(f"   Status: {status_data['status']} - {status_data['message']}")
                
                if status_data['status'] in ['completed', 'failed']:
                    break
                
                time.sleep(5)
            
            # Test 5: Download processed file if completed
            if status_data['status'] == 'completed':
                print("📥 Downloading processed file...")
                download_response = requests.get(f"{BASE_URL}/download/{file_id}?file_type=processed")
                if download_response.status_code == 200:
                    processed_data = download_response.json()
                    print(f"✓ Downloaded processed file ({len(processed_data['content'])} characters)")
                    print(f"   First 200 characters: {processed_data['content'][:200]}...")
                else:
                    print("✗ Failed to download processed file")
        else:
            print(f"✗ Failed to upload PDF: {response.text}")
    else:
        print("⚠ No test PDF found. Please place a PDF file in the current directory to test upload.")
    
    print("\n" + "=" * 50)
    print("API test completed!")

if __name__ == "__main__":
    test_api()
