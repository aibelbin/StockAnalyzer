#!/usr/bin/env python3
"""
Cleanup script to organize files that are stuck in the wrong locations due to
incomplete file movement logic in the StockAnalyzer pipeline.

This script will:
1. Move PDFs with _processed_ocr suffix to processed_pdfs folder
2. Move OCR processed files from ocr_processed_final to csv_completed folder
3. Create proper directory structure
"""

import os
import shutil
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def move_processed_pdfs():
    """Move PDFs with _processed_ocr suffix to processed_pdfs folder"""
    corporate_filings_dir = "/home/fox/Documents/StockAnalyzer/webScraper/corporate_filings_pdfs"
    processed_pdfs_dir = os.path.join(corporate_filings_dir, "processed_pdfs")
    
    # Create processed_pdfs directory if it doesn't exist
    os.makedirs(processed_pdfs_dir, exist_ok=True)
    
    moved_count = 0
    
    if not os.path.exists(corporate_filings_dir):
        logger.warning(f"Corporate filings directory not found: {corporate_filings_dir}")
        return moved_count
    
    for filename in os.listdir(corporate_filings_dir):
        if filename.endswith("_processed_ocr.pdf"):
            source_path = os.path.join(corporate_filings_dir, filename)
            dest_path = os.path.join(processed_pdfs_dir, filename)
            
            try:
                shutil.move(source_path, dest_path)
                logger.info(f"Moved: {filename} -> processed_pdfs/")
                moved_count += 1
            except Exception as e:
                logger.error(f"Failed to move {filename}: {e}")
    
    logger.info(f"Moved {moved_count} processed PDF files to processed_pdfs folder")
    return moved_count

def move_ocr_processed_files():
    """Move OCR processed files from ocr_processed_final to csv_completed folder"""
    ocr_processed_dir = "/home/fox/Documents/StockAnalyzer/ocr_processed_final"
    csv_completed_dir = os.path.join(ocr_processed_dir, "csv_completed")
    
    # Create csv_completed directory if it doesn't exist
    os.makedirs(csv_completed_dir, exist_ok=True)
    
    moved_count = 0
    
    if not os.path.exists(ocr_processed_dir):
        logger.warning(f"OCR processed directory not found: {ocr_processed_dir}")
        return moved_count
    
    for filename in os.listdir(ocr_processed_dir):
        if filename.endswith("_processed.md"):
            source_path = os.path.join(ocr_processed_dir, filename)
            dest_path = os.path.join(csv_completed_dir, filename)
            
            # Skip if it's already in a subdirectory
            if os.path.isfile(source_path):
                try:
                    shutil.move(source_path, dest_path)
                    logger.info(f"Moved: {filename} -> csv_completed/")
                    moved_count += 1
                    
                    # Look for corresponding raw OCR file
                    potential_raw_filename = filename.replace("_processed.md", "__raw_ocr_output.txt")
                    raw_source_path = os.path.join(ocr_processed_dir, potential_raw_filename)
                    if os.path.exists(raw_source_path):
                        raw_dest_path = os.path.join(csv_completed_dir, potential_raw_filename)
                        shutil.move(raw_source_path, raw_dest_path)
                        logger.info(f"Also moved raw OCR file: {potential_raw_filename}")
                        
                except Exception as e:
                    logger.error(f"Failed to move {filename}: {e}")
    
    logger.info(f"Moved {moved_count} OCR processed files to csv_completed folder")
    return moved_count

def cleanup_duplicate_processed_files():
    """Remove any remaining files that might be duplicates or stuck"""
    corporate_filings_dir = "/home/fox/Documents/StockAnalyzer/webScraper/corporate_filings_pdfs"
    
    # Count remaining _processed_ocr files
    remaining_processed = 0
    if os.path.exists(corporate_filings_dir):
        for filename in os.listdir(corporate_filings_dir):
            if filename.endswith("_processed_ocr.pdf"):
                remaining_processed += 1
    
    logger.info(f"Files remaining with _processed_ocr suffix: {remaining_processed}")
    return remaining_processed

def main():
    """Main cleanup function"""
    logger.info("Starting StockAnalyzer file organization cleanup...")
    logger.info("=" * 60)
    
    # Step 1: Move processed PDFs
    logger.info("Step 1: Moving processed PDF files...")
    moved_pdfs = move_processed_pdfs()
    
    # Step 2: Move OCR processed files
    logger.info("\nStep 2: Moving OCR processed files...")
    moved_ocr = move_ocr_processed_files()
    
    # Step 3: Check for remaining files
    logger.info("\nStep 3: Checking for remaining processed files...")
    remaining = cleanup_duplicate_processed_files()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("CLEANUP SUMMARY:")
    logger.info(f"  • Moved PDFs to processed_pdfs: {moved_pdfs}")
    logger.info(f"  • Moved OCR files to csv_completed: {moved_ocr}")
    logger.info(f"  • Remaining _processed_ocr PDFs: {remaining}")
    
    if remaining > 0:
        logger.warning("Some processed PDF files still remain in the main directory.")
        logger.warning("These might need manual review.")
    
    if moved_pdfs > 0 or moved_ocr > 0:
        logger.info("\nCleanup completed successfully!")
        logger.info("The StockAnalyzer pipeline should now work more efficiently.")
    else:
        logger.info("\nNo files needed to be moved - organization looks good!")

if __name__ == "__main__":
    main()
