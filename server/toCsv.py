import os
import json
import csv
import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Dict, Optional, List
from decouple import Config as DecoupleConfig, RepositoryEnv


try:
    config = DecoupleConfig(RepositoryEnv('.env'))
except:
    config = DecoupleConfig()

OLLAMA_BASE_URL = config.get("OLLAMA_BASE_URL", default="http://localhost:11434", cast=str)
OLLAMA_MODEL = config.get("OLLAMA_MODEL", default="llama3:8b-instruct-q4_K_M", cast=str)
OLLAMA_TIMEOUT = config.get("OLLAMA_TIMEOUT", default=0, cast=int)

PROCESSED_FOLDER = "./ocr_processed_final"
CSV_FILE = "./companies.csv"


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Consider yourself one of the best intraday equity traders in India, with a proven track record of analyzing a company's freshly published quarterly results along with its historical stock behavior to decide whether to take a trade on the same day.

I will provide you with distinct pieces of information for a specific company, the extracted text content of its freshly published quarterly results PDF released today. I want you to analyze this and generate a json response, the response should only have two parameters, {"company_name":"[the name of the company]", "description":"[a 100 word description about the company which could be used to see if it's worth taking an intraday trade today for this company, with clear, data-backed reasoning derived only from the text and historical data provided. Also, highlight the key financial figures or announcements from the report]"}

IMPORTANT: Respond ONLY with valid JSON in the exact format specified. Do not include any explanation, introduction, or additional text."""

async def call_ollama_api(prompt: str) -> Optional[str]:
    """Call Ollama API with the given prompt"""
    try:
        timeout = aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT if OLLAMA_TIMEOUT > 0 else None)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent JSON output
                    "top_p": 0.9,
                }
            }
            
            async with session.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    generated_text = result.get("response", "").strip()
                    logger.info(f"Generated {len(generated_text)} characters from Ollama")
                    return generated_text
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error {response.status}: {error_text}")
                    return None
                    
    except asyncio.TimeoutError:
        logger.error(f"Ollama request timed out")
        return None
    except Exception as e:
        logger.error(f"Error calling Ollama API: {e}")
        return None

def extract_json_from_response(response: str) -> Optional[Dict]:
    """Extract and parse JSON from the LLM response"""
    try:
        # Try to find JSON in the response
        response = response.strip()
        
        # Look for JSON brackets
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = response[start_idx:end_idx + 1]
            parsed_json = json.loads(json_str)
            
            # Validate required fields
            if "company_name" in parsed_json and "description" in parsed_json:
                return parsed_json
            else:
                logger.warning("JSON missing required fields: company_name or description")
                return None
        else:
            logger.warning("No valid JSON found in response")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        return None

async def analyze_quarterly_results(file_path: str) -> Optional[Dict]:
    """Analyze a quarterly results file and return trading analysis"""
    try:
        logger.info(f"Analyzing file: {file_path}")
        
        # Read the processed markdown file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.warning(f"File {file_path} is empty")
            return None
        
        # Create the full prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\nQuarterly Results Text:\n{content}\n\nJSON Response:"
        
        # Get analysis from Ollama
        response = await call_ollama_api(full_prompt)
        
        if not response:
            logger.error(f"No response from Ollama for {file_path}")
            return None
        
        # Extract JSON from response
        analysis = extract_json_from_response(response)
        
        if analysis:
            logger.info(f"Successfully analyzed {file_path}: {analysis['company_name']}")
            return analysis
        else:
            logger.error(f"Failed to extract valid JSON from response for {file_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return None

def ensure_csv_exists():
    """Ensure the companies.csv file exists with proper headers"""
    if not os.path.exists(CSV_FILE):
        logger.info(f"Creating new CSV file: {CSV_FILE}")
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['company_name', 'description'])
    else:
        logger.info(f"CSV file already exists: {CSV_FILE}")

def append_to_csv(analysis: Dict):
    """Append analysis results to the CSV file"""
    try:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                analysis['company_name'],
                analysis['description']
            ])
        logger.info(f"Added {analysis['company_name']} to CSV")
    except Exception as e:
        logger.error(f"Error writing to CSV: {e}")

def get_processed_files() -> List[str]:
    """Get list of processed markdown files"""
    processed_files = []
    
    if not os.path.exists(PROCESSED_FOLDER):
        logger.warning(f"Processed folder not found: {PROCESSED_FOLDER}")
        return processed_files
    
    for file in os.listdir(PROCESSED_FOLDER):
        if file.endswith('.md'):
            file_path = os.path.join(PROCESSED_FOLDER, file)
            processed_files.append(file_path)
    
    logger.info(f"Found {len(processed_files)} processed files")
    return processed_files

async def process_all_files():
    """Process all markdown files and generate CSV entries"""
    logger.info("Starting batch processing of quarterly results...")
    
    # Ensure CSV file exists
    ensure_csv_exists()
    
    # Get list of processed files
    files = get_processed_files()
    
    if not files:
        logger.warning("No processed files found to analyze")
        return
    
    successful_analyses = 0
    failed_analyses = 0
    
    for file_path in files:
        logger.info(f"Processing {os.path.basename(file_path)}...")
        
        try:
            analysis = await analyze_quarterly_results(file_path)
            
            if analysis:
                append_to_csv(analysis)
                successful_analyses += 1
            else:
                failed_analyses += 1
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            failed_analyses += 1
    
    logger.info(f"Processing complete. Success: {successful_analyses}, Failed: {failed_analyses}")
    logger.info(f"Results saved to: {CSV_FILE}")

async def process_single_file(file_path: str):
    """Process a single file and add to CSV"""
    logger.info(f"Processing single file: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    # Ensure CSV file exists
    ensure_csv_exists()
    
    # Process the file
    analysis = await analyze_quarterly_results(file_path)
    
    if analysis:
        append_to_csv(analysis)
        logger.info("File processed successfully")
    else:
        logger.error("Failed to process file")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        # Process specific file
        file_path = sys.argv[1]
        asyncio.run(process_single_file(file_path))
    else:
        # Process all files
        asyncio.run(process_all_files())

if __name__ == "__main__":
    main()
