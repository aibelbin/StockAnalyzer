import os
import json
import csv
import asyncio
import aiohttp
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, List

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_NUM_THREAD
except ImportError:
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:8b")
    OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "0"))  # 0 = no timeout
    OLLAMA_NUM_THREAD = int(os.environ.get("OLLAMA_NUM_THREAD", "8"))

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SERVER_DIR)
PROCESSED_FOLDER = os.path.join(ROOT_DIR, "ocr_processed_final")
CSV_FILE = os.path.join(ROOT_DIR, "companies.csv")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SYSTEM_PROMPT_NEW = """Consider yourself one of the best intraday equity traders in India, with a proven track record of analyzing a company's freshly published quarterly results along with its historical stock behavior to decide whether to take a trade on the same day.

I will provide you with distinct pieces of information for a specific company, the extracted text content of its freshly published quarterly results PDF released today. I want you to analyze this and generate a json response, the response should only have two parameters, {"company_name":"[the name of the company]", "description":"[a 100 word description about the company which could be used to see if it's worth taking an intraday trade today for this company, with clear, data-backed reasoning derived only from the text and historical data provided. Also, highlight the key financial figures or announcements from the report]"}

CRITICAL INSTRUCTIONS:
- Respond with ONLY valid JSON - no explanations, no introductions, no additional text
- Use exactly this format: {"company_name": "Company Name", "description": "Your 100-word analysis here"}
- Do not include any text before or after the JSON
- Ensure the JSON is properly formatted with quotes around keys and values"""

SYSTEM_PROMPT_UPDATE = """Consider yourself one of the best intraday equity traders in India, with a proven track record of analyzing a company's freshly published quarterly results along with its historical stock behavior to decide whether to take a trade on the same day.

I will provide you with distinct pieces of information for a specific company:
1. OLD ANALYSIS: The previous trading analysis description for this company
2. NEW DATA: The extracted text content of its freshly published quarterly results PDF released today

Compare the old analysis with the new quarterly results data and generate an UPDATED json response with two parameters, {"company_name":"[the name of the company]", "description":"[a 100 word UPDATED description incorporating both historical analysis and new quarterly results, focusing on what's changed, new developments, and current intraday trade potential based on the latest data]"}

CRITICAL INSTRUCTIONS:
- Respond with ONLY valid JSON - no explanations, no introductions, no additional text
- Use exactly this format: {"company_name": "Company Name", "description": "Your 100-word updated analysis here"}
- Do not include any text before or after the JSON
- Ensure the JSON is properly formatted with quotes around keys and values"""

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
                    "temperature": 0.1,  # Very low temperature for consistent JSON output
                    "top_p": 0.8,
                    "repeat_penalty": 1.1,
                    "num_predict": 500,
                    "num_thread": OLLAMA_NUM_THREAD,  # Use all 8 CPU cores
                    "num_ctx": 4096,  # Larger context window
                }
            }
            
            async with session.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    generated_text = result.get("response", "").strip()
                    logger.info(f"Generated {len(generated_text)} characters from Ollama using {OLLAMA_NUM_THREAD} threads")
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
    """Extract and parse JSON from the LLM response with improved error handling"""
    try:
        response = response.strip()
        
        
        logger.debug(f"Parsing response: {response[:200]}...")
        
       
        json_candidates = []
        
      
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_candidates.append(response[start_idx:end_idx + 1])
        
       
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                json_candidates.append(line)
        
        
        import re
        json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        json_candidates.extend(json_blocks)
        
      
        for candidate in json_candidates:
            try:
                parsed_json = json.loads(candidate.strip())
                
               
                if isinstance(parsed_json, dict) and "company_name" in parsed_json and "description" in parsed_json:
                    logger.debug(f"Successfully parsed JSON: {parsed_json['company_name']}")
                    return parsed_json
                else:
                    logger.debug(f"JSON missing required fields: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'not a dict'}")
                    
            except json.JSONDecodeError as e:
                logger.debug(f"JSON parse failed for candidate: {str(e)}")
                continue
        
        logger.warning(f"No valid JSON found. Response sample: {response[:500]}...")
        return None
            
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        logger.debug(f"Full response was: {response}")
        return None

def get_existing_companies() -> Dict[str, str]:
    existing_companies = {}
    
    if not os.path.exists(CSV_FILE):
        logger.info(f"CSV file does not exist yet: {CSV_FILE}")
        return existing_companies
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                logger.info(f"CSV file exists but is empty: {CSV_FILE}")
                return existing_companies
        
        first_line = lines[0].strip()
        has_headers = first_line.lower().startswith('company_name') and 'description' in first_line.lower()
        
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            if has_headers:
                reader = csv.DictReader(f)
                rows = list(reader)
            else:
                logger.warning(f"CSV file missing headers, treating all lines as data: {CSV_FILE}")
                reader = csv.reader(f)
                rows = []
                for row in reader:
                    if len(row) >= 2:  # Ensure we have at least 2 columns
                        rows.append({
                            'company_name': row[0].strip(),
                            'description': row[1].strip() if len(row) > 1 else ''
                        })
            
            if not rows:
                logger.info(f"CSV file exists but has no data rows: {CSV_FILE}")
                return existing_companies
                
            for row in rows:
                company_name = row.get('company_name', '').strip()
                description = row.get('description', '').strip()
                if company_name:
                    existing_companies[company_name.lower()] = description
        
        logger.info(f"Found {len(existing_companies)} existing companies in CSV: {CSV_FILE}")
        
    except Exception as e:
        logger.error(f"Error reading existing CSV {CSV_FILE}: {e}")
    
    return existing_companies

def update_csv_entry(company_name: str, new_description: str):
    """Update existing company entry in CSV"""
    try:
        rows = []
        fieldnames = ['company_name', 'description']
        
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or fieldnames
                rows = list(reader)
        
        updated = False
        for row in rows:
            if row['company_name'].lower() == company_name.lower():
                row['description'] = new_description
                updated = True
                break
        
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        if updated:
            logger.info(f"Updated existing entry for: {company_name}")
        else:
            logger.warning(f"Company not found for update: {company_name}")
            
    except Exception as e:
        logger.error(f"Error updating CSV entry: {e}")

async def analyze_quarterly_results(file_path: str) -> Optional[Dict]:
    """Analyze a quarterly results file and return trading analysis"""
    try:
        logger.info(f"Analyzing file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.warning(f"File {file_path} is empty")
            return None
        
        existing_companies = get_existing_companies()
        
        preliminary_prompt = f"{SYSTEM_PROMPT_NEW}\n\nQuarterly Results Text:\n{content[:2000]}...\n\nJSON Response:"
        preliminary_response = await call_ollama_api(preliminary_prompt)
        
        if preliminary_response:
            preliminary_analysis = extract_json_from_response(preliminary_response)
            if preliminary_analysis and 'company_name' in preliminary_analysis:
                company_name = preliminary_analysis['company_name'].strip()
                company_key = company_name.lower()
                
                if company_key in existing_companies:
                    logger.info(f"Company {company_name} exists. Updating analysis...")
                    old_description = existing_companies[company_key]
                    
                    full_prompt = f"""{SYSTEM_PROMPT_UPDATE}

OLD ANALYSIS:
{old_description}

NEW DATA - Quarterly Results Text:
{content}

JSON Response:"""
                    
                else:
                    logger.info(f"New company {company_name}. Creating fresh analysis...")
                    full_prompt = f"{SYSTEM_PROMPT_NEW}\n\nQuarterly Results Text:\n{content}\n\nJSON Response:"
            else:
                logger.warning("Could not extract company name from preliminary analysis")
                full_prompt = f"{SYSTEM_PROMPT_NEW}\n\nQuarterly Results Text:\n{content}\n\nJSON Response:"
                response = await call_ollama_api(full_prompt)
        else:
            logger.warning("Preliminary analysis failed, using new company prompt")
            full_prompt = f"{SYSTEM_PROMPT_NEW}\n\nQuarterly Results Text:\n{content}\n\nJSON Response:"
        
        response = await call_ollama_api(full_prompt)
        
        if not response:
            logger.error(f"No response from Ollama for {file_path}")
            return None
        
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
    abs_csv_path = os.path.abspath(CSV_FILE)
    
    if not os.path.exists(CSV_FILE):
        logger.info(f"Creating new CSV file: {abs_csv_path}")
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['company_name', 'description'])
    else:
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                
            if not (first_line.lower().startswith('company_name') and 'description' in first_line.lower()):
                logger.info(f"Fixing CSV file headers: {abs_csv_path}")
                
                existing_data = []
                with open(CSV_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            existing_data.append([row[0].strip(), row[1].strip()])
                
                with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['company_name', 'description'])
                    writer.writerows(existing_data)
                
                logger.info(f"Fixed CSV file with {len(existing_data)} existing entries")
            else:
                logger.info(f"CSV file already exists with proper headers: {abs_csv_path}")
                
        except Exception as e:
            logger.error(f"Error checking/fixing CSV headers: {e}")

def add_or_update_csv(analysis: Dict):
    """Add new entry or update existing entry in CSV"""
    try:
        company_name = analysis['company_name'].strip()
        description = analysis['description'].strip()
        
        existing_companies = get_existing_companies()
        company_key = company_name.lower()
        
        if company_key in existing_companies:
            update_csv_entry(company_name, description)
            logger.info(f"Updated existing company: {company_name}")
        else:
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([company_name, description])
            logger.info(f"Added new company: {company_name}")
            
    except Exception as e:
        logger.error(f"Error adding/updating CSV: {e}")

def append_to_csv(analysis: Dict):
    """Legacy function - now calls add_or_update_csv"""
    add_or_update_csv(analysis)

def get_processed_files() -> List[str]:
    """Get list of processed markdown files"""
    processed_files = []
    
    abs_processed_folder = os.path.abspath(PROCESSED_FOLDER)
    
    if not os.path.exists(PROCESSED_FOLDER):
        logger.warning(f"Processed folder not found: {abs_processed_folder}")
        logger.info("Make sure you have run the FastAPI server and processed some PDFs first.")
        logger.info("The FastAPI server should create this folder and save processed .md files there.")
        return processed_files
    
    try:
        for file in os.listdir(PROCESSED_FOLDER):
            if file.endswith('.md'):
                file_path = os.path.join(PROCESSED_FOLDER, file)
                processed_files.append(file_path)
        
        logger.info(f"Found {len(processed_files)} processed files in: {abs_processed_folder}")
        
        if len(processed_files) == 0:
            logger.warning("No .md files found in the processed folder.")
            logger.info("Upload some PDFs to the FastAPI server first to generate processed files.")
            
    except Exception as e:
        logger.error(f"Error reading processed folder: {e}")
    
    return processed_files

async def process_all_files():
    """Process all markdown files and generate CSV entries"""
    logger.info("Starting batch processing of quarterly results...")
    
    ensure_csv_exists()
    
    files = get_processed_files()
    
    if not files:
        logger.warning("No processed files found to analyze")
        return
    
    existing_companies = get_existing_companies()
    logger.info(f"Starting with {len(existing_companies)} existing companies in CSV")
    
    successful_analyses = 0
    failed_analyses = 0
    updated_companies = 0
    new_companies = 0
    
    for file_path in files:
        logger.info(f"Processing {os.path.basename(file_path)}...")
        
        try:
            analysis = await analyze_quarterly_results(file_path)
            
            if analysis:
                company_name = analysis['company_name'].strip()
                company_key = company_name.lower()
                
                if company_key in existing_companies:
                    updated_companies += 1
                else:
                    new_companies += 1
                
                add_or_update_csv(analysis)
                successful_analyses += 1
            else:
                failed_analyses += 1
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            failed_analyses += 1
    
    logger.info(f"Processing complete:")
    logger.info(f"  Success: {successful_analyses}, Failed: {failed_analyses}")
    logger.info(f"  New companies: {new_companies}, Updated companies: {updated_companies}")
    logger.info(f"Results saved to: {CSV_FILE}")

async def process_single_file(file_path: str):
    """Process a single file and add to CSV"""
    logger.info(f"Processing single file: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    ensure_csv_exists()
    
    existing_companies = get_existing_companies()
    
    analysis = await analyze_quarterly_results(file_path)
    
    if analysis:
        company_name = analysis['company_name'].strip()
        company_key = company_name.lower()
        
        if company_key in existing_companies:
            logger.info(f"Updating existing company: {company_name}")
        else:
            logger.info(f"Adding new company: {company_name}")
        
        add_or_update_csv(analysis)
        logger.info("File processed successfully")
    else:
        logger.error("Failed to process file")

def main():
    """Main function"""
    import sys
    
    abs_processed_folder = os.path.abspath(PROCESSED_FOLDER)
    abs_csv_file = os.path.abspath(CSV_FILE)
    
    print("Stock Analyzer - Quarterly Results to CSV Processor")
    print("=" * 55)
    print(f"Looking for processed files in: {abs_processed_folder}")
    print(f"CSV output will be saved to: {abs_csv_file}")
    print()
    
    if os.path.exists(abs_csv_file):
        try:
            with open(abs_csv_file, 'r') as f:
                lines = f.readlines()
                if len(lines) <= 1:  # Only header or empty
                    print(f"CSV file exists but is empty (only headers)")
                else:
                    print(f"CSV file contains {len(lines)-1} existing entries")
        except Exception as e:
            print(f"Error reading CSV file: {e}")
    else:
        print("CSV file does not exist yet - will be created")
    print()
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROCESSED_FOLDER, file_path)
        
        print(f"Processing single file: {file_path}")
        asyncio.run(process_single_file(file_path))
    else:
        print("Processing all .md files in the processed folder...")
        asyncio.run(process_all_files())

if __name__ == "__main__":
    main()
