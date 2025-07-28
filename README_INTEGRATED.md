# Stock Analyzer - Integrated System

This is a comprehensive stock analysis system that automatically scrapes NSE announcements, processes PDF documents with OCR, and generates trading analysis using AI.

## System Architecture

The integrated system consists of 4 main components that run simultaneously:

1. **NSE Web Scraper** (`webScraper/nseindia.py`)
   - Continuously monitors NSE website for new announcements
   - Downloads PDF files to `corporate_filings_pdfs/` folder
   - Runs every 30 seconds

2. **FastAPI Server** (`server/fastapi.py`)
   - Web API for PDF processing with OCR
   - Background processing with status tracking
   - Runs on `http://localhost:8000`

3. **PDF Feeder** (`server/feeder.py`)
   - Automatically uploads PDFs from scraped folder to FastAPI server
   - Renames processed files with `_processed_ocr` suffix
   - Runs every 5 minutes

4. **CSV Processor** (`server/toCsv.py`)
   - Processes OCR results using AI (Ollama LLM)
   - Generates trading analysis and saves to `companies.csv`
   - Runs every 10 minutes

## Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Ollama** running locally with a model (e.g., `llama3:8b-instruct-q4_K_M`)
3. **Tesseract OCR** installed on your system

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure Ollama is running:
```bash
ollama serve
ollama pull llama3:8b-instruct-q4_K_M
```

### Running the System

**Option 1: Simplified Startup (Recommended)**
```bash
python start.py
```

**Option 2: Direct Orchestrator**
```bash
python run_server.py
```

The system will automatically:
- Create necessary directories
- Start all components
- Begin monitoring and processing

### Monitoring the System

**Check System Health:**
```bash
python health_check.py
```

**View Logs:**
- Main log: `stockanalyzer.log`
- Feeder log: `server/feeder.log`

**Check FastAPI API:**
- Visit: `http://localhost:8000/docs`
- Test upload: `http://localhost:8000/`

## Directory Structure

```
stockanalyzer/
├── run_server.py              # Main orchestrator
├── start.py                   # Simplified startup script
├── health_check.py            # System health checker
├── requirements.txt           # Python dependencies
├── companies.csv              # Generated analysis results
├── stockanalyzer.log          # Main system log
│
├── corporate_filings_pdfs/    # Downloaded PDFs from NSE
├── uploaded_pdfs/             # PDFs uploaded to FastAPI
├── ocr_processed_final/       # OCR processed results
│
├── webScraper/
│   └── nseindia.py           # NSE scraper
│
└── server/
    ├── fastapi.py            # FastAPI web server
    ├── feeder.py             # PDF uploader
    ├── toCsv.py              # CSV generator
    └── config.py             # Configuration
```

## Workflow

1. **NSE Scraper** downloads new PDF announcements
2. **Feeder** detects new PDFs and uploads them to **FastAPI Server**
3. **FastAPI Server** processes PDFs with OCR in background
4. **CSV Processor** analyzes OCR results with AI and updates CSV

## Configuration

Key configuration files:
- `config.py` - Ollama settings
- `server/config.py` - Server-specific settings

Environment variables (optional):
- `OLLAMA_BASE_URL` (default: http://localhost:11434)
- `OLLAMA_MODEL` (default: llama3:8b-instruct-q4_K_M)
- `OLLAMA_TIMEOUT` (default: 0)

## Stopping the System

Press `Ctrl+C` to stop all components gracefully.

## Troubleshooting

### Common Issues

1. **FastAPI server not starting:**
   - Check if port 8000 is available
   - Run: `python health_check.py`

2. **NSE scraper not working:**
   - Check internet connection
   - Verify NSE website accessibility

3. **OCR processing fails:**
   - Ensure Tesseract is installed
   - Check if `pdf2image` dependencies are available

4. **CSV generation fails:**
   - Verify Ollama is running
   - Check if the correct model is available

### Logs

- **Main system:** `stockanalyzer.log`
- **PDF feeder:** `server/feeder.log`
- **Console output:** Real-time status updates

### Manual Operations

**Upload single PDF:**
```bash
curl -X POST "http://localhost:8000/upload_pdf" -F "file=@document.pdf"
```

**Check processing status:**
```bash
curl "http://localhost:8000/status/YOUR_FILE_ID"
```

**Process single OCR file:**
```bash
cd server
python toCsv.py filename.md
```

**Run PDF feeder once:**
```bash
cd server  
python feeder.py
```

## Features

- **Automated PDF Discovery:** Continuously monitors NSE for new announcements
- **Background Processing:** No timeouts for large PDF files
- **Status Tracking:** Real-time processing status with polling
- **Duplicate Prevention:** Automatically skips already processed files
- **AI Analysis:** Uses Ollama LLM for trading insights
- **Robust Error Handling:** Automatic retries and graceful failures
- **Comprehensive Logging:** Detailed logs for debugging

## API Endpoints

- `GET /` - System status
- `POST /upload_pdf` - Upload PDF for processing
- `GET /status/{file_id}` - Check processing status
- `GET /docs` - API documentation

## Contributing

1. Ensure all components work independently
2. Test the integrated system with `python health_check.py`
3. Check logs for any errors
4. Update documentation as needed

## License

[Your License Here]
