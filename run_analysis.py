

import os
import asyncio
import sys

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from toCsv import process_all_files, process_single_file

def main():
    """Example usage"""
    print("Stock Analyzer - Quarterly Results to CSV Processor")
    print("=" * 50)
    
    # Check if processed files exist
    processed_folder = "./ocr_processed_final"
    if not os.path.exists(processed_folder):
        print(f"Error: Processed folder not found: {processed_folder}")
        print("Please run the FastAPI server and process some PDFs first.")
        return
    
    # Count files
    md_files = [f for f in os.listdir(processed_folder) if f.endswith('.md')]
    print(f"Found {len(md_files)} processed markdown files")
    
    if len(md_files) == 0:
        print("No processed files found. Upload some PDFs to the FastAPI server first.")
        return
    
    print("\nFiles found:")
    for i, file in enumerate(md_files[:5], 1):  # Show first 5 files
        print(f"  {i}. {file}")
    if len(md_files) > 5:
        print(f"  ... and {len(md_files) - 5} more")
    
    print(f"\nProcessing all files and generating companies.csv...")
    
    # Process all files
    asyncio.run(process_all_files())
    
    # Check if CSV was created
    csv_file = "./companies.csv"
    if os.path.exists(csv_file):
        print(f"\nSuccess! Results saved to: {csv_file}")
        
        # Show a preview of the CSV
        try:
            import csv
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
            print(f"CSV contains {len(rows) - 1} companies (excluding header)")
            print("\nPreview (first 3 entries):")
            print("-" * 80)
            
            for i, row in enumerate(rows[:4]):  # Header + first 3 entries
                if i == 0:
                    print(f"{'Company Name':<30} | Description")
                    print("-" * 80)
                else:
                    company = row[0][:28] + "..." if len(row[0]) > 30 else row[0]
                    desc = row[1][:45] + "..." if len(row[1]) > 45 else row[1]
                    print(f"{company:<30} | {desc}")
                    
        except Exception as e:
            print(f"Error reading CSV preview: {e}")
    else:
        print("Error: CSV file was not created")

if __name__ == "__main__":
    main()
