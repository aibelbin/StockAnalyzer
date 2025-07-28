import os
import json
import csv
import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Dict, Optional, List


try:
    from decouple import Config as DecoupleConfig, RepositoryEnv
    if os.path.exists('.env'):
        config = DecoupleConfig(RepositoryEnv('.env'))
    else:
        # Create a mock config class for fallback
        class MockConfig:
            def get(self, key: str, default=None, cast=str):
                return cast(os.environ.get(key, default))
        config = MockConfig()
except ImportError:
    # Fallback if decouple is not installed
    class MockConfig:
        def get(self, key: str, default=None, cast=str):
            return cast(os.environ.get(key, default))
    config = MockConfig()

OLLAMA_BASE_URL = config.get("OLLAMA_BASE_URL", default="http://localhost:11434", cast=str)
OLLAMA_MODEL = config.get("OLLAMA_MODEL", default="llama3:8b-instruct-q4_K_M", cast=str)
OLLAMA_TIMEOUT = config.get("OLLAMA_TIMEOUT", default=0, cast=int)

PROCESSED_FOLDER = "./ocr_processed_final"
CSV_FILE = "./companies.csv"


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



SYSTEM_PROMPT_NEW = """Consider yourself one of the best intraday equity traders in India, with a proven track record of analyzing a company's freshly published quarterly results along with its historical stock behavior to decide whether to take a trade on the same day.

I will provide you with distinct pieces of information for a specific company, the extracted text content of its freshly published quarterly results PDF released today. I want you to analyze this and generate a json response, the response should only have two parameters, {"company_name":"[the name of the company]", "description":"[a 100 word description about the company which could be used to see if it's worth taking an intraday trade today for this company, with clear, data-backed reasoning derived only from the text and historical data provided. Also, highlight the key financial figures or announcements from the report]"}

IMPORTANT: Respond ONLY with valid JSON in the exact format specified. Do not include any explanation, introduction, or additional text."""


SYSTEM_PROMPT_UPDATE = """Consider yourself one of the best intraday equity traders in India, with a proven track record of analyzing a company's freshly published quarterly results along with its historical stock behavior to decide whether to take a trade on the same day.

I will provide you with distinct pieces of information for a specific company:
1. OLD ANALYSIS: The previous trading analysis description for this company
2. NEW DATA: The extracted text content of its freshly published quarterly results PDF released today

Compare the old analysis with the new quarterly results data and generate an UPDATED json response with two parameters, {"company_name":"[the name of the company]", "description":"[a 100 word UPDATED description incorporating both historical analysis and new quarterly results, focusing on what's changed, new developments, and current intraday trade potential based on the latest data]"}

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
        
        response = response.strip()
        
       
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = response[start_idx:end_idx + 1]
            parsed_json = json.loads(json_str)
            
            
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

def get_existing_companies() -> Dict[str, str]:
    """Get existing companies and their descriptions from CSV"""
    existing_companies = {}
    
    if not os.path.exists(CSV_FILE):
        return existing_companies
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                company_name = row.get('company_name', '').strip()
                description = row.get('description', '').strip()
                if company_name:
                    existing_companies[company_name.lower()] = description
        
        logger.info(f"Found {len(existing_companies)} existing companies in CSV")
        
    except Exception as e:
        logger.error(f"Error reading existing CSV: {e}")
    
    return existing_companies

def update_csv_entry(company_name: str, new_description: str):
    """Update existing company entry in CSV"""
    try:
        # Read all rows
        rows = []
        fieldnames = ['company_name', 'description']
        
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or fieldnames
                rows = list(reader)
        
        # Update the specific company row
        updated = False
        for row in rows:
            if row['company_name'].lower() == company_name.lower():
                row['description'] = new_description
                updated = True
                break
        
        # Write back to CSV
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
        
        # Read the processed markdown file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.warning(f"File {file_path} is empty")
            return None
        
        # Get existing companies
        existing_companies = get_existing_companies()
        
        # First, try to extract company name from the content to check if it exists
        # We'll do a preliminary analysis to get the company name
        preliminary_prompt = f"{SYSTEM_PROMPT_NEW}\n\nQuarterly Results Text:\n{content[:2000]}...\n\nJSON Response:"
        preliminary_response = await call_ollama_api(preliminary_prompt)
        
        if preliminary_response:
            preliminary_analysis = extract_json_from_response(preliminary_response)
            if preliminary_analysis and 'company_name' in preliminary_analysis:
                company_name = preliminary_analysis['company_name'].strip()
                company_key = company_name.lower()
                
                # Check if company exists
                if company_key in existing_companies:
                    logger.info(f"Company {company_name} exists. Updating analysis...")
                    old_description = existing_companies[company_key]
                    
                    # Use update prompt with old and new data
                    full_prompt = f"""{SYSTEM_PROMPT_UPDATE}

OLD ANALYSIS:
{old_description}

NEW DATA - Quarterly Results Text:
{content}

JSON Response:"""
                    
                else:
                    logger.info(f"New company {company_name}. Creating fresh analysis...")
                    # Use new company prompt
                    full_prompt = f"{SYSTEM_PROMPT_NEW}\n\nQuarterly Results Text:\n{content}\n\nJSON Response:"
            else:
                logger.warning("Could not extract company name from preliminary analysis")
                # Fallback to new company prompt
                full_prompt = f"{SYSTEM_PROMPT_NEW}\n\nQuarterly Results Text:\n{content}\n\nJSON Response:"
        else:
            logger.warning("Preliminary analysis failed, using new company prompt")
            full_prompt = f"{SYSTEM_PROMPT_NEW}\n\nQuarterly Results Text:\n{content}\n\nJSON Response:"
        
        # Get final analysis from Ollama
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

def add_or_update_csv(analysis: Dict):
    """Add new entry or update existing entry in CSV"""
    try:
        company_name = analysis['company_name'].strip()
        description = analysis['description'].strip()
        
        # Get existing companies
        existing_companies = get_existing_companies()
        company_key = company_name.lower()
        
        if company_key in existing_companies:
            # Update existing entry
            update_csv_entry(company_name, description)
            logger.info(f"Updated existing company: {company_name}")
        else:
            # Add new entry
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
    
    # Get existing companies for summary
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
                
                # Check if this was an update or new entry
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
    
    # Ensure CSV file exists
    ensure_csv_exists()
    
    # Get existing companies for logging
    existing_companies = get_existing_companies()
    
    # Process the file
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
    
    if len(sys.argv) > 1:
       
        file_path = sys.argv[1]
        asyncio.run(process_single_file(file_path))
    else:
       
        asyncio.run(process_all_files())

if __name__ == "__main__":
    main()
