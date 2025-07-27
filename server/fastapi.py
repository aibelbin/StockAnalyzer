from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
from datetime import datetime
import sys
import logging

# Add the tools directory to the path to import transformer_img
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
from transformer_img import process_pdf_file

app = FastAPI()

# Configuration
UPLOAD_FOLDER = "./uploaded_pdfs"
PROCESSED_FOLDER = "./ocr_processed_final"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_progress(message: str):
    """Print progress messages to terminal"""
    print(f"[OCR Processing] {message}")
    logger.info(message)

@app.get("/")
def default():
    return {"message": "Stock Analyzer PDF OCR Service", "version": "2.0", "status": "Streamlined workflow active"}

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file and process it immediately"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Generate unique file ID and timestamp
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create safe filename
        safe_filename = f"{timestamp}_{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        print_progress(f"Uploading file: {file.filename}")
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print_progress(f"File saved: {safe_filename}")
        print_progress("Starting OCR processing...")
        
        # Process the PDF immediately
        result = await process_pdf_file(file_path)
        
        if result:
            # Move processed files to the final directory
            processed_filename = f"{timestamp}_{file_id}_{os.path.splitext(file.filename)[0]}_processed.md"
            final_processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
            
            # Copy the processed file to the final directory
            if os.path.exists(result["processed_file"]):
                shutil.copy2(result["processed_file"], final_processed_path)
                print_progress(f"Processed file saved to: {final_processed_path}")
            
            print_progress("Processing completed successfully")
            
            return JSONResponse(content={
                "status": "success",
                "message": "PDF processed successfully",
                "file_id": file_id,
                "original_filename": file.filename,
                "processed_file_path": final_processed_path,
                "quality_score": result.get("quality_score"),
                "pages_processed": result.get("pages_processed"),
                "processing_stats": {
                    "raw_text_length": result.get("raw_text_length"),
                    "processed_text_length": result.get("processed_text_length")
                }
            })
        else:
            print_progress("Processing failed - no result returned")
            raise HTTPException(status_code=500, detail="PDF processing failed")
            
    except Exception as e:
        error_msg = f"Error processing PDF: {str(e)}"
        print_progress(error_msg)
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
