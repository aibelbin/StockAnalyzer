# Stock Analyzer PDF OCR API - Streamlined Workflow

## Overview

This FastAPI service provides automated PDF OCR processing with immediate results. Upload a PDF and get the processed markdown file automatically saved to the `ocr_processed_final` folder.

**Version 2.0 - Streamlined Workflow**
- No manual status checking required
- No UUID copying needed
- Automatic file processing and saving
- Terminal progress display
- Professional logging without emojis

## Quick Start

1. Start the server:
```bash
cd /path/to/stockanalyzer
python3 run_server.py
```

2. Upload and process a PDF:
```bash
curl -X POST "http://localhost:8000/upload_pdf" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf"
```

3. Find your processed file in the `ocr_processed_final` folder.

## API Endpoints

### GET /
**Description:** Get server status and version information

**Response:**
```json
{
  "message": "Stock Analyzer PDF OCR Service",
  "version": "2.0",
  "status": "Streamlined workflow active"
}
```

### POST /upload_pdf
**Description:** Upload a PDF file and process it immediately

**Parameters:**
- `file` (required): PDF file to upload

**Response on Success:**
```json
{
  "status": "success",
  "message": "PDF processed successfully",
  "file_id": "abc123-def456-ghi789",
  "original_filename": "document.pdf",
  "processed_file_path": "./ocr_processed_final/20250127_143022_abc123_document_processed.md",
  "quality_score": 85,
  "pages_processed": 10,
  "processing_stats": {
    "raw_text_length": 50000,
    "processed_text_length": 48000
  }
}
```

**Response on Error:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Workflow

1. **Upload**: Send PDF file to `/upload_pdf`
2. **Processing**: Server immediately processes the PDF (watch terminal for progress)
3. **Results**: Get immediate response with file location and quality metrics
4. **File Access**: Find processed markdown file in `ocr_processed_final` folder

## Progress Monitoring

Processing progress is displayed in the terminal where the server is running:
```
[OCR Processing] Uploading file: document.pdf
[OCR Processing] File saved: 20250127_143022_abc123_document.pdf
[OCR Processing] Starting OCR processing...
Processing chunk 1/5 (8000 chars)... Complete (7800 chars)
Processing chunk 2/5 (7500 chars)... Complete (7200 chars)
...
All 5 chunks processed successfully
[OCR Processing] Processed file saved to: ./ocr_processed_final/20250127_143022_abc123_document_processed.md
[OCR Processing] Processing completed successfully
```

## Error Handling

Common error responses:

- **400 Bad Request**: Invalid file type (only PDFs allowed)
- **500 Internal Server Error**: Processing failed (check logs for details)

## File Organization

```
stockanalyzer/
├── uploaded_pdfs/          # Original uploaded PDFs
├── ocr_processed_final/    # Final processed markdown files
├── server/
│   └── fastapi.py         # Main API server
└── tools/
    └── transformer_img.py # OCR processing engine
```

## Testing

Use the provided test script:
```bash
python3 test_streamlined_api.py document.pdf
```

## Configuration

Environment variables (create `.env` file):
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b-instruct-q4_K_M
OLLAMA_TIMEOUT=0
```

## Requirements

- Python 3.8+
- FastAPI
- Ollama running locally
- Poppler utilities for PDF processing
- Tesseract OCR

## Key Improvements in v2.0

- **Eliminated Background Tasks**: Processing happens synchronously
- **Removed Manual Steps**: No more status checking or manual downloading
- **Automated File Management**: Files automatically saved to final directory
- **Professional Logging**: Clean terminal output without emojis
- **Simplified API**: Single endpoint for complete workflow

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install System Dependencies

For Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

For macOS:
```bash
brew install tesseract poppler
```

### 3. Setup Ollama
1. Install Ollama from https://ollama.ai/
2. Pull the required model:
```bash
ollama pull llama3:8b-instruct-q4_K_M
```

### 4. Start Processing
```bash
python3 run_server.py
```

The streamlined workflow is now ready for use!
