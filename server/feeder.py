
import requests
import os
import time
import logging
from pathlib import Path
from typing import List, Optional

API_BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{API_BASE_URL}/upload_pdf"
STATUS_ENDPOINT = f"{API_BASE_URL}/status"

if os.path.exists("../webScraper/corporate_filings_pdfs"):
    PDF_SOURCE_FOLDER = "../webScraper/corporate_filings_pdfs"
elif os.path.exists("./webScraper/corporate_filings_pdfs"):
    PDF_SOURCE_FOLDER = "./webScraper/corporate_filings_pdfs"
else:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    PDF_SOURCE_FOLDER = os.path.join(project_root, "webScraper", "corporate_filings_pdfs")

PROCESSED_SUFFIX = "_processed_ocr"
STATUS_CHECK_INTERVAL = 300

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./feeder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_pdf_files() -> List[str]:
    pdf_files = []
    
    source_path = os.path.abspath(PDF_SOURCE_FOLDER)
    
    if not os.path.exists(source_path):
        logger.error(f"Source folder not found: {source_path}")
        return pdf_files
    
    try:
        for file in os.listdir(source_path):
            if file.lower().endswith('.pdf'):
                # Skip files that already have _processed_ocr suffix
                if '_processed_ocr.pdf' in file:
                    logger.debug(f"Skipping already processed file: {file}")
                    continue
                    
                file_path = os.path.join(source_path, file)
                pdf_files.append(file_path)
        
        logger.info(f"Found {len(pdf_files)} PDF files to process in: {source_path}")
        
    except Exception as e:
        logger.error(f"Error reading PDF folder: {e}")
    
    return pdf_files

def is_already_processed(pdf_path: str) -> bool:
    try:
        directory = os.path.dirname(pdf_path)
        filename = os.path.basename(pdf_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        processed_filename = f"{name_without_ext}{PROCESSED_SUFFIX}.pdf"
        processed_path = os.path.join(directory, processed_filename)
        
        if os.path.exists(processed_path):
            logger.info(f"Already processed: {filename} -> {processed_filename}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking if file is processed: {e}")
        return False

def mark_as_processed(pdf_path: str) -> bool:
    try:
        directory = os.path.dirname(pdf_path)
        filename = os.path.basename(pdf_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        processed_filename = f"{name_without_ext}{PROCESSED_SUFFIX}.pdf"
        processed_path = os.path.join(directory, processed_filename)
        
        os.rename(pdf_path, processed_path)
        logger.info(f"Marked as processed: {filename} -> {processed_filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error marking file as processed: {e}")
        return False

def upload_pdf(pdf_path: str) -> bool:
    try:
        filename = os.path.basename(pdf_path)
        logger.info(f"Uploading: {filename}")
        
        try:
            status_response = requests.get(API_BASE_URL, timeout=10)
            if status_response.status_code != 200:
                logger.error(f"Server not responding properly: {status_response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Cannot connect to server: {e}")
            return False
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            
            logger.info(f"Starting upload of {filename}...")
            response = requests.post(
                UPLOAD_ENDPOINT, 
                files=files, 
                timeout=60
            )
        
        if response.status_code != 200:
            logger.error(f"Upload failed for {filename}")
            logger.error(f"  Status Code: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False
        
        result = response.json()
        file_id = result.get('file_id')
        
        if not file_id:
            logger.error(f"No file ID returned for {filename}")
            return False
        
        logger.info(f"Upload successful: {filename}")
        logger.info(f"  File ID: {file_id}")
        logger.info(f"  Status: {result.get('status', 'unknown')}")
        
        return wait_for_processing_completion(file_id, filename)
            
    except requests.exceptions.Timeout:
        logger.error(f"Upload timeout for {filename}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Upload error for {filename}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error uploading {filename}: {e}")
        return False

def wait_for_processing_completion(file_id: str, filename: str) -> bool:
    logger.info(f"Waiting for processing completion of {filename}...")
    
    check_count = 0
    max_checks = 60
    
    while check_count < max_checks:
        try:
            status_url = f"{STATUS_ENDPOINT}/{file_id}"
            response = requests.get(status_url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Status check failed for {filename}: {response.status_code}")
                return False
            
            status_data = response.json()
            current_status = status_data.get('status', 'unknown')
            progress = status_data.get('progress', 0)
            message = status_data.get('message', 'No message')
            
            logger.info(f"  Status check {check_count + 1}: {current_status} ({progress}%) - {message}")
            
            if current_status == 'completed':
                logger.info(f"Processing completed successfully for {filename}")
                processed_path = status_data.get('processed_file_path', 'N/A')
                quality_score = status_data.get('quality_score', 'N/A')
                pages_processed = status_data.get('pages_processed', 'N/A')
                
                logger.info(f"  Processed file saved to: {processed_path}")
                logger.info(f"  Quality Score: {quality_score}")
                logger.info(f"  Pages Processed: {pages_processed}")
                return True
            
            elif current_status == 'failed':
                error_msg = status_data.get('error', 'Unknown error')
                logger.error(f"Processing failed for {filename}: {error_msg}")
                return False
            
            elif current_status in ['uploaded', 'processing']:
                check_count += 1
                logger.info(f"  Still processing... waiting {STATUS_CHECK_INTERVAL} seconds before next check")
                time.sleep(STATUS_CHECK_INTERVAL)
            
            else:
                logger.warning(f"Unknown status '{current_status}' for {filename}")
                check_count += 1
                time.sleep(STATUS_CHECK_INTERVAL)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking status for {filename}: {e}")
            check_count += 1
            time.sleep(STATUS_CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Unexpected error checking status for {filename}: {e}")
            check_count += 1
            time.sleep(STATUS_CHECK_INTERVAL)
    
    logger.error(f"Processing timeout for {filename} after {max_checks} status checks")
    return False

def process_all_pdfs():
    logger.info("Starting PDF processing workflow...")
    logger.info(f"Source folder: {os.path.abspath(PDF_SOURCE_FOLDER)}")
    logger.info(f"API endpoint: {UPLOAD_ENDPOINT}")
    logger.info("=" * 60)
    
    pdf_files = get_pdf_files()
    
    if not pdf_files:
        logger.warning("No PDF files found to process")
        return
    
    total_files = len(pdf_files)
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    successful_count = 0
    
    logger.info(f"Found {total_files} PDF files to process")
    
    for i, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        logger.info(f"\n[{i}/{total_files}] Processing: {filename}")
        
        if is_already_processed(pdf_path):
            logger.info(f"Skipping (already processed): {filename}")
            skipped_count += 1
            continue
        
        success = upload_pdf(pdf_path)
        
        if success:
            if mark_as_processed(pdf_path):
                successful_count += 1
                logger.info(f"Successfully processed: {filename}")
            else:
                logger.warning(f"Upload succeeded but failed to mark as processed: {filename}")
                successful_count += 1
        else:
            failed_count += 1
            logger.error(f"Failed to process: {filename}")
        
        processed_count += 1
        
        if i < total_files:
            logger.info("Waiting 5 seconds before next upload")
            time.sleep(5)
    
    logger.info("\n" + "=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info(f"Total files found: {total_files}")
    logger.info(f"Already processed (skipped): {skipped_count}")
    logger.info(f"Successfully uploaded: {successful_count}")
    logger.info(f"Failed uploads: {failed_count}")
    logger.info(f"Files processed this run: {processed_count}")

def main():
    try:
        process_all_pdfs()
    except KeyboardInterrupt:
        logger.info("\nProcessing interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")

if __name__ == "__main__":
    main()
