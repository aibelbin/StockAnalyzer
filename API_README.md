# Stock Analyzer PDF OCR API

This FastAPI service provides OCR (Optical Character Recognition) processing for PDF files using Tesseract and LLM-based text correction via Ollama.

## Features

- **PDF Upload**: Upload PDF files via REST API
- **Automatic OCR Processing**: Convert PDF pages to text using Tesseract
- **LLM Text Correction**: Clean and format OCR output using Ollama
- **Markdown Formatting**: Optional markdown formatting of processed text
- **Quality Assessment**: Automatic quality scoring of the OCR results
- **Background Processing**: Non-blocking file processing
- **Status Monitoring**: Real-time processing status updates

## Setup

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
ollama pull llama3.2:3b
```

### 4. Configuration

Copy the environment template and configure:
```bash
cp .env.template .env
```

Edit `.env` with your settings:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=300
```

## Running the Server

### Option 1: Using the startup script
```bash
python run_server.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn server.fastapi:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

## API Endpoints

### 1. Health Check
```
GET /
```
Returns server status and version information.

### 2. List Processing Status
```
GET /acquired_pdfs
```
Returns the processing status of all uploaded PDFs.

### 3. Upload PDF
```
POST /upload_pdf
```
Upload a PDF file for processing.

**Parameters:**
- `file`: PDF file (multipart/form-data)

**Response:**
```json
{
  "message": "PDF uploaded successfully and queued for processing",
  "file_id": "uuid-string",
  "filename": "document.pdf",
  "status": "uploaded"
}
```

### 4. Check Processing Status
```
GET /status/{file_id}
```
Get the current processing status of a specific file.

**Response:**
```json
{
  "filename": "document.pdf",
  "upload_time": "2025-07-27T10:30:00",
  "status": "completed",
  "message": "PDF processed successfully",
  "file_path": "/path/to/uploaded/file.pdf",
  "result": {
    "raw_ocr_file": "/path/to/raw_ocr.txt",
    "processed_file": "/path/to/processed.md",
    "quality_score": 85,
    "explanation": "Good quality processing with minor corrections needed"
  }
}
```

**Status Values:**
- `uploaded`: File uploaded, queued for processing
- `processing`: OCR and LLM processing in progress
- `completed`: Processing completed successfully
- `failed`: Processing failed with error

### 5. Download Processed Files
```
GET /download/{file_id}?file_type={type}
```

**Parameters:**
- `file_type`: Either `raw_ocr` or `processed`

**Response:**
```json
{
  "file_id": "uuid-string",
  "file_type": "processed",
  "content": "# Document Title\n\nProcessed content...",
  "file_path": "/path/to/processed/file.md"
}
```

## Example Usage

### Using curl

1. Upload a PDF:
```bash
curl -X POST "http://localhost:8000/upload_pdf" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.pdf"
```

2. Check status:
```bash
curl -X GET "http://localhost:8000/status/{file_id}"
```

3. Download processed file:
```bash
curl -X GET "http://localhost:8000/download/{file_id}?file_type=processed"
```

### Using Python requests

```python
import requests

# Upload PDF
with open('document.pdf', 'rb') as f:
    files = {'file': ('document.pdf', f, 'application/pdf')}
    response = requests.post('http://localhost:8000/upload_pdf', files=files)
    result = response.json()
    file_id = result['file_id']

# Check status
status_response = requests.get(f'http://localhost:8000/status/{file_id}')
status_data = status_response.json()

# Download processed file
if status_data['status'] == 'completed':
    download_response = requests.get(f'http://localhost:8000/download/{file_id}?file_type=processed')
    processed_content = download_response.json()['content']
```

## Testing

Run the test script to verify everything is working:
```bash
python test_api.py
```

## File Structure

```
stockanalyzer/
├── server/
│   └── fastapi.py          # FastAPI server implementation
├── tools/
│   └── transformer_img.py  # OCR and LLM processing functions
├── uploaded_pdfs/          # Uploaded PDF files (created automatically)
├── processed_pdfs/         # Processed output files (created automatically)
├── run_server.py          # Server startup script
├── test_api.py            # API testing script
├── requirements.txt       # Python dependencies
└── .env.template         # Environment configuration template
```

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**: Ensure Ollama is running and the model is available
2. **Tesseract Not Found**: Install tesseract-ocr system package
3. **PDF Conversion Error**: Install poppler-utils system package
4. **Memory Issues**: Large PDFs may require more RAM, consider processing in smaller batches

### Logs

Check the server logs for detailed error information. The API uses structured logging for debugging.

## Performance Notes

- OCR processing time depends on PDF size and page count
- LLM processing adds significant time but improves text quality
- Processing happens in background, allowing multiple uploads
- Consider adjusting `OLLAMA_TIMEOUT` for large documents

## Security Considerations

- The API currently doesn't implement authentication
- Uploaded files are stored on the server filesystem
- Consider implementing file cleanup for production use
- Add rate limiting for production deployments
