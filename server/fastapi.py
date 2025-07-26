from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import shutil
import asyncio
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
PROCESSED_FOLDER = "./processed_pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Store processing status
processing_status = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_pdf_background(file_id: str, pdf_path: str):
    """Background task to process PDF"""
    try:
        processing_status[file_id]["status"] = "processing"
        processing_status[file_id]["message"] = "OCR processing started"
        
        # Process the PDF using the OCR transformer
        result = await process_pdf_file(pdf_path)
        
        if result:
            processing_status[file_id]["status"] = "completed"
            processing_status[file_id]["message"] = "PDF processed successfully"
            processing_status[file_id]["result"] = {
                "raw_ocr_file": result["raw_ocr_file"],
                "processed_file": result["processed_file"],
                "quality_score": result.get("quality_score"),
                "explanation": result.get("explanation")
            }
        else:
            processing_status[file_id]["status"] = "failed"
            processing_status[file_id]["message"] = "PDF processing failed"
            
    except Exception as e:
        logger.error(f"Error processing PDF {file_id}: {str(e)}")
        processing_status[file_id]["status"] = "failed"
        processing_status[file_id]["message"] = f"Processing error: {str(e)}"

@app.get("/")
def default():
    return {"message": "Stock Analyzer PDF OCR Service", "version": "1.0"}

@app.get("/acquired_pdfs")
def list_pdfs():
    """List all uploaded PDFs and their processing status"""
    return {"processing_status": processing_status}

@app.post("/upload_pdf")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a PDF file for OCR processing"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create safe filename
        safe_filename = f"{timestamp}_{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Initialize processing status
        processing_status[file_id] = {
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "status": "uploaded",
            "message": "File uploaded successfully, queued for processing",
            "file_path": file_path
        }
        
        # Start background processing
        background_tasks.add_task(process_pdf_background, file_id, file_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "PDF uploaded successfully and queued for processing",
                "file_id": file_id,
                "filename": file.filename,
                "status": "uploaded"
            }
        )
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/status/{file_id}")
async def get_processing_status(file_id: str):
    """Get the processing status of a specific PDF"""
    
    if file_id not in processing_status:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    return processing_status[file_id]

@app.get("/download/{file_id}")
async def download_processed_file(file_id: str, file_type: str = "processed"):
    """Download processed files (raw_ocr or processed)"""
    
    if file_id not in processing_status:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    status_info = processing_status[file_id]
    
    if status_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="File processing not completed")
    
    if "result" not in status_info:
        raise HTTPException(status_code=400, detail="No processed files available")
    
    result = status_info["result"]
    
    if file_type == "raw_ocr" and "raw_ocr_file" in result:
        file_path = result["raw_ocr_file"]
    elif file_type == "processed" and "processed_file" in result:
        file_path = result["processed_file"]
    else:
        raise HTTPException(status_code=400, detail="Invalid file type or file not available")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Return file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return JSONResponse(
        status_code=200,
        content={
            "file_id": file_id,
            "file_type": file_type,
            "content": content,
            "file_path": file_path
        }
    )
    
