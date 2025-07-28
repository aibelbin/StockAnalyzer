from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
from datetime import datetime
import sys
import logging
import asyncio

# Add the tools directory to the path to import transformer_img
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
from transformer_img import process_pdf_file

app = FastAPI()

# Configuration
UPLOAD_FOLDER = "./uploaded_pdfs"
PROCESSED_FOLDER = "./ocr_processed_final"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Store processing status
processing_status = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_progress(message: str):
    """Print progress messages to terminal"""
    print(f"[OCR Processing] {message}")
    logger.info(message)

async def process_pdf_background(file_id: str, pdf_path: str, original_filename: str):
    """Background task to process PDF"""
    try:
        processing_status[file_id]["status"] = "processing"
        processing_status[file_id]["message"] = "OCR processing started"
        processing_status[file_id]["progress"] = 0
        
        print_progress(f"Starting background processing for: {original_filename}")
        
        # Process the PDF using the OCR transformer
        result = await process_pdf_file(pdf_path)
        
        if result:
            # Move processed files to the final directory
            timestamp = processing_status[file_id]["timestamp"]
            processed_filename = f"{timestamp}_{file_id}_{os.path.splitext(original_filename)[0]}_processed.md"
            final_processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
            
            # Copy the processed file to the final directory
            if os.path.exists(result["processed_file"]):
                shutil.copy2(result["processed_file"], final_processed_path)
                print_progress(f"Processed file saved to: {final_processed_path}")
            
            processing_status[file_id]["status"] = "completed"
            processing_status[file_id]["message"] = "PDF processed successfully"
            processing_status[file_id]["progress"] = 100
            processing_status[file_id]["result"] = {
                "processed_file_path": final_processed_path,
                "quality_score": result.get("quality_score"),
                "pages_processed": result.get("pages_processed"),
                "raw_text_length": result.get("raw_text_length"),
                "processed_text_length": result.get("processed_text_length")
            }
            
            print_progress(f"Background processing completed for: {original_filename}")
            
        else:
            processing_status[file_id]["status"] = "failed"
            processing_status[file_id]["message"] = "PDF processing failed - no result returned"
            processing_status[file_id]["progress"] = 0
            
    except Exception as e:
        error_msg = f"Error processing PDF {file_id}: {str(e)}"
        print_progress(error_msg)
        logger.error(error_msg)
        processing_status[file_id]["status"] = "failed"
        processing_status[file_id]["message"] = f"Processing error: {str(e)}"
        processing_status[file_id]["progress"] = 0

@app.get("/")
def default():
    return {"message": "Stock Analyzer PDF OCR Service", "version": "2.0", "status": "Background processing active"}

@app.post("/upload_pdf")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a PDF file for background processing"""
    
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
        
        # Initialize processing status
        processing_status[file_id] = {
            "filename": file.filename,
            "timestamp": timestamp,
            "upload_time": datetime.now().isoformat(),
            "status": "uploaded",
            "message": "File uploaded successfully, processing queued",
            "progress": 0,
            "file_path": file_path
        }
        
        # Start background processing
        background_tasks.add_task(process_pdf_background, file_id, file_path, file.filename)
        
        print_progress(f"File saved and queued for processing: {safe_filename}")
        
        return JSONResponse(content={
            "status": "uploaded",
            "message": "PDF uploaded successfully and queued for processing",
            "file_id": file_id,
            "original_filename": file.filename,
            "processing_status": "queued"
        })
        
    except Exception as e:
        error_msg = f"Error uploading PDF: {str(e)}"
        print_progress(error_msg)
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/status/{file_id}")
def get_processing_status(file_id: str):
    """Get the processing status of a specific file"""
    if file_id not in processing_status:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    status_info = processing_status[file_id].copy()
    
    # Add helpful status information
    if status_info["status"] == "completed":
        status_info["ready_for_next"] = True
    else:
        status_info["ready_for_next"] = False
    
    return status_info

@app.get("/status")
def get_all_processing_status():
    """Get the processing status of all files"""
    return {
        "total_files": len(processing_status),
        "processing_status": processing_status,
        "active_processing": sum(1 for status in processing_status.values() if status["status"] == "processing"),
        "completed": sum(1 for status in processing_status.values() if status["status"] == "completed"),
        "failed": sum(1 for status in processing_status.values() if status["status"] == "failed")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
