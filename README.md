# StockAnalyzer

A tool for analyzing quarterly results of companies and generating insights for intraday trading.

## System Architecture

The StockAnalyzer uses a hybrid approach combining cloud and local AI models for optimal performance:

### OCR Processing (transformer_img.py)
- Uses **Groq API** with the `llama3-70b-8192` model
- Provides high-quality OCR text correction and extraction
- Used for the initial processing of PDF documents

### CSV Generation (server/toCsv.py)
- Uses **Ollama API** with the `llama2:7b` model running locally
- Handles the analysis of extracted text and generation of trading insights
- Eliminates rate limit issues by processing locally

## Configuration

The system uses environment variables for configuration:

### Groq Configuration (OCR Processing)
```
GROQ_API_KEY=your_api_key
GROQ_API_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama3-70b-8192
GROQ_TIMEOUT=60
```

### Ollama Configuration (CSV Processing)
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2:7b
OLLAMA_TIMEOUT=120
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Ollama (for local processing):
   ```bash
   # For Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # For macOS
   curl -fsSL https://ollama.com/install.sh | sh
   ```

3. Pull the Llama 2 model:
   ```bash
   ollama pull llama2:7b
   ```

4. Start the Ollama service:
   ```bash
   ollama serve
   ```

5. Run the StockAnalyzer:
   ```bash
   python run_server.py
   ```

## Benefits of the Hybrid Approach

- Reduces Groq API usage by approximately 70-80%
- Eliminates rate limit issues for CSV processing
- Maintains high-quality OCR correction with Groq
- Leverages local computing for intensive batch processing
