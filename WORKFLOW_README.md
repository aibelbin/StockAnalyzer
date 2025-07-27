# Stock Analyzer - Complete PDF to CSV Trading Analysis Workflow

## Overview

This system provides a complete pipeline from PDF quarterly results to trading analysis CSV:

1. **FastAPI Server**: OCR processes PDFs → Markdown files
2. **Analysis Script**: Markdown files → Trading analysis → CSV

## Workflow

### Step 1: Process PDFs with OCR
```bash
# Start the FastAPI server
python run_server.py

# Upload PDFs (they get processed automatically)
curl -X POST "http://localhost:8000/upload_pdf" \
     -F "file=@quarterly_results.pdf"
```

### Step 2: Generate Trading Analysis CSV
```bash
# Process all markdown files and generate companies.csv
python server/toCsv.py

# Or process a specific file
python server/toCsv.py ./ocr_processed_final/specific_file.md

# Or use the example runner
python run_analysis.py
```

## File Structure

```
stockanalyzer/
├── uploaded_pdfs/          # Original PDFs
├── ocr_processed_final/    # OCR-processed markdown files
├── companies.csv           # Final trading analysis CSV
├── server/
│   ├── fastapi.py         # PDF OCR API server
│   └── toCsv.py           # Markdown → CSV processor
├── run_server.py          # Start FastAPI server
└── run_analysis.py        # Example analysis runner
```

## Output Format

The `companies.csv` file contains:

| Column | Description |
|--------|-------------|
| company_name | Name of the company from quarterly results |
| description | 100-word trading analysis with key financial figures |

Example CSV content:
```csv
company_name,description
"Reliance Industries","Strong Q3 performance with revenue growth of 15% YoY to ₹2.3L crores. Retail segment showed resilience with 12% growth. Petrochemicals margin improved to 8.2%. Digital services ARPU increased to ₹154. Debt reduced by ₹15,000 crores. Capex guidance maintained at ₹75,000 crores. Positive outlook for oil-to-chemicals integration. Key risk: Global crude volatility. Intraday trade potential: High due to strong fundamentals and positive guidance."
```

## System Prompt

The analysis uses this trading-focused prompt:

> "Consider yourself one of the best intraday equity traders in India, with a proven track record of analyzing a company's freshly published quarterly results along with its historical stock behavior to decide whether to take a trade on the same day..."

## Usage Examples

### Process All Files
```bash
cd /path/to/stockanalyzer
python server/toCsv.py
```

### Process Single File
```bash
python server/toCsv.py ./ocr_processed_final/20250127_143022_abc123_company_processed.md
```

### View Results
```bash
# Check the generated CSV
cat companies.csv

# Or use the example runner for a nice preview
python run_analysis.py
```

## Configuration

Set up your `.env` file:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b-instruct-q4_K_M
OLLAMA_TIMEOUT=0
```

## Requirements

Make sure you have:
- Ollama running locally with the specified model
- All dependencies installed (`pip install -r requirements.txt`)
- At least one processed markdown file in `ocr_processed_final/`

## Complete Example Workflow

```bash
# 1. Start the OCR server
python run_server.py &

# 2. Upload some PDFs
curl -X POST "http://localhost:8000/upload_pdf" -F "file=@company1.pdf"
curl -X POST "http://localhost:8000/upload_pdf" -F "file=@company2.pdf"

# 3. Generate trading analysis CSV
python server/toCsv.py

# 4. View results
python run_analysis.py
```

Your `companies.csv` file will now contain trading analysis for each company based on their quarterly results!
