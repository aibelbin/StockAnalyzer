import os
import traceback
import asyncio
import json
import re
import logging
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
import warnings
from typing import List, Dict, Tuple, Optional
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError, PDFInfoNotInstalledError, PDFSyntaxError
import pytesseract
import numpy as np
from PIL import Image
from decouple import Config as DecoupleConfig, RepositoryEnv
import cv2
import aiohttp
    
import cv2
import aiohttp
import sys

# Add parent directory to path for config import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import configuration
try:
    from config import GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL, GROQ_TIMEOUT
    print(f"DEBUG: Loaded from config.py - GROQ_MODEL: {GROQ_MODEL}")
except ImportError as e:
    print(f"DEBUG: Config import failed: {e}")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
    GROQ_API_URL = os.environ.get("GROQ_API_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama3-70b-8192")
    GROQ_TIMEOUT = int(os.environ.get("GROQ_TIMEOUT", "60"))
    print(f"DEBUG: Using environment fallback - GROQ_MODEL: {GROQ_MODEL}")

print(f"DEBUG: Final GROQ_MODEL setting: {GROQ_MODEL}")

warnings.filterwarnings("ignore", category=FutureWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Groq API Functions
async def generate_completion(prompt: str, max_tokens: int = 4000) -> Optional[str]:
    """Generate completion using Groq API"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=GROQ_TIMEOUT)) as session:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
            }
            
            async with session.post(f"{GROQ_API_URL}/chat/completions", headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    generated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    logging.info(f"Generated {len(generated_text)} characters with Groq using model: {GROQ_MODEL}")
                    return generated_text
                else:
                    error_text = await response.text()
                    logging.error(f"Groq API error {response.status}: {error_text}")
                    return None
                    
    except asyncio.TimeoutError:
        logging.error(f"Groq request timed out after {GROQ_TIMEOUT} seconds")
        return None
    except Exception as e:
        logging.error(f"Error calling Groq API: {e}")
        return None

def estimate_tokens(text: str) -> int:
    """Simple token estimation - roughly 4 characters per token"""
    return len(text) // 4

def chunk_text(text: str, max_chunk_size: int = 8000) -> List[str]:
    """Split text into chunks that fit within token limits"""
    # Split by paragraphs first
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        
        if current_length + paragraph_length <= max_chunk_size:
            current_chunk.append(paragraph)
            current_length += paragraph_length
        else:
            # Save current chunk if it has content
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            
            # If paragraph is too long, split it by sentences
            if paragraph_length > max_chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                current_chunk = []
                current_length = 0
                
                for sentence in sentences:
                    sentence_length = len(sentence)
                    if current_length + sentence_length <= max_chunk_size:
                        current_chunk.append(sentence)
                        current_length += sentence_length
                    else:
                        if current_chunk:
                            chunks.append(' '.join(current_chunk))
                        current_chunk = [sentence]
                        current_length = sentence_length
            else:
                current_chunk = [paragraph]
                current_length = paragraph_length
    
    # Add remaining content
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk) if len(current_chunk) > 1 else current_chunk[0])
    
    return chunks

# Image Processing Functions
def preprocess_image(image):
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    kernel = np.ones((1, 1), np.uint8)
    gray = cv2.dilate(gray, kernel, iterations=1)
    return Image.fromarray(gray)

def repair_pdf_with_gs(input_pdf_path: str, output_pdf_path: str) -> bool:
    """
    Attempt to repair a corrupted PDF using Ghostscript
    """
    try:
        logging.info(f"Attempting to repair PDF: {input_pdf_path}")
        
        # Check if Ghostscript is available
        gs_command = None
        for cmd in ['gs', 'ghostscript', 'gswin64c', 'gswin32c']:
            if shutil.which(cmd):
                gs_command = cmd
                break
        
        if not gs_command:
            logging.warning("Ghostscript not found. Cannot repair PDF.")
            return False
        
        # Ghostscript command to repair PDF
        repair_command = [
            gs_command,
            '-o', output_pdf_path,
            '-sDEVICE=pdfwrite',
            '-dPDFSETTINGS=/prepress',
            '-dNOPAUSE',
            '-dBATCH',
            '-dSAFER',
            '-dCompatibilityLevel=1.4',
            input_pdf_path
        ]
        
        result = subprocess.run(repair_command, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_pdf_path):
            logging.info(f"PDF successfully repaired: {output_pdf_path}")
            return True
        else:
            logging.error(f"PDF repair failed. Return code: {result.returncode}")
            logging.error(f"Stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error("PDF repair timed out")
        return False
    except Exception as e:
        logging.error(f"Error repairing PDF: {e}")
        return False

def convert_pdf_to_images_with_retry(input_pdf_file_path: str, max_pages: int = 0, skip_first_n_pages: int = 0) -> List[Image.Image]:
    """
    Convert PDF to images with error handling and repair attempts
    """
    logging.info(f"Processing PDF file {input_pdf_file_path}")
    
    if max_pages == 0:
        last_page = None
        logging.info("Converting all pages to images...")
    else:
        last_page = skip_first_n_pages + max_pages
        logging.info(f"Converting pages {skip_first_n_pages + 1} to {last_page}")
    
    first_page = skip_first_n_pages + 1
    
    # First attempt: try to convert directly
    try:
        images = convert_from_path(input_pdf_file_path, first_page=first_page, last_page=last_page)
        logging.info(f"Converted {len(images)} pages from PDF file to images.")
        return images
        
    except (PDFPageCountError, PDFSyntaxError, Exception) as e:
        logging.warning(f"Initial PDF conversion failed: {e}")
        
        # Second attempt: try to repair the PDF first
        base_name = os.path.splitext(input_pdf_file_path)[0]
        repaired_pdf_path = f"{base_name}_repaired.pdf"
        
        if repair_pdf_with_gs(input_pdf_file_path, repaired_pdf_path):
            try:
                logging.info("Attempting conversion with repaired PDF...")
                images = convert_from_path(repaired_pdf_path, first_page=first_page, last_page=last_page)
                logging.info(f"Successfully converted {len(images)} pages from repaired PDF.")
                
                # Clean up repaired file
                try:
                    os.remove(repaired_pdf_path)
                    logging.info("Cleaned up temporary repaired PDF")
                except:
                    pass
                    
                return images
                
            except Exception as e2:
                logging.error(f"Conversion failed even with repaired PDF: {e2}")
                
                # Clean up repaired file
                try:
                    os.remove(repaired_pdf_path)
                except:
                    pass
        
        # Third attempt: try with different parameters
        try:
            logging.info("Attempting conversion with reduced quality settings...")
            images = convert_from_path(
                input_pdf_file_path, 
                first_page=first_page, 
                last_page=last_page,
                dpi=150,  # Reduced DPI
                fmt='jpeg',  # Different format
                thread_count=1  # Single thread
            )
            logging.info(f"Converted {len(images)} pages with reduced settings.")
            return images
            
        except Exception as e3:
            logging.error(f"All conversion attempts failed: {e3}")
            
            # Fourth attempt: try to convert only the first page
            try:
                logging.info("Attempting to convert only the first page...")
                images = convert_from_path(
                    input_pdf_file_path,
                    first_page=1,
                    last_page=1,
                    dpi=150
                )
                if images:
                    logging.warning(f"Only converted first page due to PDF corruption. Original request was for pages {first_page}-{last_page}")
                    return images
                    
            except Exception as e4:
                logging.error(f"Even single page conversion failed: {e4}")
        
        # If all attempts fail, raise the original error
        raise Exception(f"PDF is severely corrupted and cannot be processed. Original error: {e}")

def convert_pdf_to_images(input_pdf_file_path: str, max_pages: int = 0, skip_first_n_pages: int = 0) -> List[Image.Image]:
    """
    Legacy function - now calls the robust version
    """
    return convert_pdf_to_images_with_retry(input_pdf_file_path, max_pages, skip_first_n_pages)

def ocr_image(image):
    preprocessed_image = preprocess_image(image)
    return pytesseract.image_to_string(preprocessed_image)

async def process_chunk(chunk: str, prev_context: str, chunk_index: int, total_chunks: int, reformat_as_markdown: bool, suppress_headers_and_page_numbers: bool) -> Tuple[str, str]:
    logging.info(f"Processing chunk {chunk_index + 1}/{total_chunks} (length: {len(chunk):,} characters)")
    
    # Step 1: OCR Correction
    ocr_correction_prompt = f"""Correct OCR-induced errors in the text, ensuring it flows coherently with the previous context. Follow these guidelines:

1. Fix OCR-induced typos and errors:
   - Correct words split across line breaks
   - Fix common OCR errors (e.g., 'rn' misread as 'm')
   - Use context and common sense to correct errors
   - Only fix clear errors, don't alter the content unnecessarily
   - Do not add extra periods or any unnecessary punctuation

2. Maintain original structure:
   - Keep all headings and subheadings intact

3. Preserve original content:
   - Keep all important information from the original text
   - Do not add any new information not present in the original text
   - Remove unnecessary line breaks within sentences or paragraphs
   - Maintain paragraph breaks
   
4. Maintain coherence:
   - Ensure the content connects smoothly with the previous context
   - Handle text that starts or ends mid-sentence appropriately

IMPORTANT: Respond ONLY with the corrected text. Preserve all original formatting, including line breaks. Do not include any introduction, explanation, or metadata.

Previous context:
{prev_context[-500:] if prev_context else ""}

Current chunk to process:
{chunk}

Corrected text:
"""
    
    ocr_corrected_chunk = await generate_completion(ocr_correction_prompt, max_tokens=len(chunk) + 500)
    if not ocr_corrected_chunk:
        logging.warning(f"Failed to get OCR correction for chunk {chunk_index + 1}, using original text")
        ocr_corrected_chunk = chunk
    
    processed_chunk = ocr_corrected_chunk

    # Step 2: Markdown Formatting (if requested)
    if reformat_as_markdown:
        markdown_prompt = f"""Reformat the following text as markdown, improving readability while preserving the original structure. Follow these guidelines:
1. Preserve all original headings, converting them to appropriate markdown heading levels (# for main titles, ## for subtitles, etc.)
   - Ensure each heading is on its own line
   - Add a blank line before and after each heading
2. Maintain the original paragraph structure. Remove all breaks within a word that should be a single word (for example, "cor- rect" should be "correct")
3. Format lists properly (unordered or ordered) if they exist in the original text
4. Use emphasis (*italic*) and strong emphasis (**bold**) where appropriate, based on the original formatting
5. Preserve all original content and meaning
6. Do not add any extra punctuation or modify the existing punctuation
7. Remove any spuriously inserted introductory text such as "Here is the corrected text:" that may have been added by the LLM and which is obviously not part of the original text.
8. Remove any obviously duplicated content that appears to have been accidentally included twice. Follow these strict guidelines:
   - Remove only exact or near-exact repeated paragraphs or sections within the main chunk.
   - Consider the context (before and after the main chunk) to identify duplicates that span chunk boundaries.
   - Do not remove content that is simply similar but conveys different information.
   - Preserve all unique content, even if it seems redundant.
   - Ensure the text flows smoothly after removal.
   - Do not add any new content or explanations.
   - If no obvious duplicates are found, return the main chunk unchanged.
9. {"Identify but do not remove headers, footers, or page numbers. Instead, format them distinctly, e.g., as blockquotes." if not suppress_headers_and_page_numbers else "Carefully remove headers, footers, and page numbers while preserving all other content."}

Text to reformat:

{ocr_corrected_chunk}

Reformatted markdown:
"""
        markdown_result = await generate_completion(markdown_prompt, max_tokens=len(ocr_corrected_chunk) + 500)
        if markdown_result:
            processed_chunk = markdown_result
        else:
            logging.warning(f"Failed to get markdown formatting for chunk {chunk_index + 1}, using OCR corrected text")
    
    new_context = processed_chunk[-1000:] if processed_chunk else ""  # Use the last 1000 characters as context for the next chunk
    logging.info(f"Chunk {chunk_index + 1}/{total_chunks} processed. Output length: {len(processed_chunk):,} characters")
    return processed_chunk, new_context

async def process_chunks(chunks: List[str], reformat_as_markdown: bool, suppress_headers_and_page_numbers: bool) -> List[str]:
    total_chunks = len(chunks)
    
    # Process chunks sequentially to maintain context
    context = ""
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        # Print progress update to console
        print(f"Processing chunk {i + 1}/{total_chunks} ({len(chunk):,} chars)... ", end='', flush=True)
        
        processed_chunk, context = await process_chunk(chunk, context, i, total_chunks, reformat_as_markdown, suppress_headers_and_page_numbers)
        processed_chunks.append(processed_chunk)
        
        # Print completion for this chunk
        print(f"Complete ({len(processed_chunk):,} chars)")
    
    print(f"All {total_chunks} chunks processed successfully")
    return processed_chunks

async def process_document(list_of_extracted_text_strings: List[str], reformat_as_markdown: bool = True, suppress_headers_and_page_numbers: bool = True) -> str:
    logging.info(f"Starting document processing. Total pages: {len(list_of_extracted_text_strings):,}")
    full_text = "\n\n".join(list_of_extracted_text_strings)
    logging.info(f"Size of full text before processing: {len(full_text):,} characters")
    chunk_size, overlap = 8000, 10
    # Improved chunking logic
    paragraphs = re.split(r'\n\s*\n', full_text)
    chunks = []
    current_chunk = []
    current_chunk_length = 0
    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        if current_chunk_length + paragraph_length <= chunk_size:
            current_chunk.append(paragraph)
            current_chunk_length += paragraph_length
        else:
            # If adding the whole paragraph exceeds the chunk size,
            # we need to split the paragraph into sentences
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            current_chunk = []
            current_chunk_length = 0
            for sentence in sentences:
                sentence_length = len(sentence)
                if current_chunk_length + sentence_length <= chunk_size:
                    current_chunk.append(sentence)
                    current_chunk_length += sentence_length
                else:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_chunk_length = sentence_length
    # Add any remaining content as the last chunk
    if current_chunk:
        chunks.append("\n\n".join(current_chunk) if len(current_chunk) > 1 else current_chunk[0])
    # Add overlap between chunks
    for i in range(1, len(chunks)):
        overlap_text = chunks[i-1].split()[-overlap:]
        chunks[i] = " ".join(overlap_text) + " " + chunks[i]
    logging.info(f"Document split into {len(chunks):,} chunks. Chunk size: {chunk_size:,}, Overlap: {overlap:,}")
    processed_chunks = await process_chunks(chunks, reformat_as_markdown, suppress_headers_and_page_numbers)
    final_text = "".join(processed_chunks)
    logging.info(f"Size of text after combining chunks: {len(final_text):,} characters")
    logging.info(f"Document processing complete. Final text length: {len(final_text):,} characters")
    return final_text

def remove_corrected_text_header(text):
    return text.replace("# Corrected text\n", "").replace("# Corrected text:", "").replace("\nCorrected text", "").replace("Corrected text:", "")

async def assess_output_quality(original_text, processed_text):
    max_chars = 15000  # Limit to avoid exceeding token limits
    available_chars_per_text = max_chars // 2  # Split equally between original and processed

    original_sample = original_text[:available_chars_per_text]
    processed_sample = processed_text[:available_chars_per_text]
    
    prompt = f"""Compare the following samples of original OCR text with the processed output and assess the quality of the processing. Consider the following factors:
1. Accuracy of error correction
2. Improvement in readability
3. Preservation of original content and meaning
4. Appropriate use of markdown formatting (if applicable)
5. Removal of hallucinations or irrelevant content

Original text sample:
```
{original_sample}
```

Processed text sample:
```
{processed_sample}
```

Provide a quality score between 0 and 100, where 100 is perfect processing. Also provide a brief explanation of your assessment.

Your response should be in the following format:
SCORE: [Your score]
EXPLANATION: [Your explanation]
"""

    response = await generate_completion(prompt, max_tokens=1000)
    
    try:
        lines = response.strip().split('\n')
        score_line = next(line for line in lines if line.startswith('SCORE:'))
        score = int(score_line.split(':')[1].strip())
        explanation = '\n'.join(line for line in lines if line.startswith('EXPLANATION:')).replace('EXPLANATION:', '').strip()
        logging.info(f"Quality assessment: Score {score}/100")
        logging.info(f"Explanation: {explanation}")
        return score, explanation
    except Exception as e:
        logging.error(f"Error parsing quality assessment response: {e}")
        logging.error(f"Raw response: {response}")
        return None, None
    
async def process_pdf_file(input_pdf_file_path: str, max_test_pages: int = 0, skip_first_n_pages: int = 0, 
                          reformat_as_markdown: bool = True, suppress_headers_and_page_numbers: bool = True) -> Optional[Dict]:
    """
    Process a PDF file through OCR and LLM correction.
    
    Args:
        input_pdf_file_path: Path to the PDF file to process
        max_test_pages: Maximum number of pages to process (0 = all pages)
        skip_first_n_pages: Number of pages to skip from the beginning
        reformat_as_markdown: Whether to format output as markdown
        suppress_headers_and_page_numbers: Whether to remove headers/footers
    
    Returns:
        Dictionary with processing results or None if failed
    """
    try:
        logging.info(f"Starting PDF processing for: {input_pdf_file_path}")
        
        # Test Groq connection
        test_response = await generate_completion("Hello, can you respond with 'Groq is working'?", max_tokens=50)
        if not test_response:
            logging.error("Failed to connect to Groq. Please ensure your API key is valid and the model is available.")
            return None

        # Generate output file paths
        base_name = os.path.splitext(input_pdf_file_path)[0]
        output_extension = '.md' if reformat_as_markdown else '.txt'
        
        raw_ocr_output_file_path = f"{base_name}__raw_ocr_output.txt"
        llm_corrected_output_file_path = base_name + '_llm_corrected' + output_extension

        # Convert PDF to images and perform OCR
        try:
            list_of_scanned_images = convert_pdf_to_images(input_pdf_file_path, max_test_pages, skip_first_n_pages)
            
            if not list_of_scanned_images:
                raise Exception("No images were extracted from the PDF")
                
            logging.info(f"Successfully extracted {len(list_of_scanned_images)} images from PDF")
            logging.info(f"Tesseract version: {pytesseract.get_tesseract_version()}")
            logging.info("Extracting text from converted pages...")
            
            with ThreadPoolExecutor() as executor:
                list_of_extracted_text_strings = list(executor.map(ocr_image, list_of_scanned_images))
            
            # Filter out empty or very short text extractions
            non_empty_texts = [text for text in list_of_extracted_text_strings if text.strip() and len(text.strip()) > 10]
            
            if not non_empty_texts:
                raise Exception("No meaningful text could be extracted from the PDF images")
            
            if len(non_empty_texts) < len(list_of_extracted_text_strings):
                logging.warning(f"Only {len(non_empty_texts)} out of {len(list_of_extracted_text_strings)} pages contained meaningful text")
            
            list_of_extracted_text_strings = non_empty_texts
            logging.info("Done extracting text from converted pages.")
            
        except Exception as pdf_error:
            logging.error(f"Failed to process PDF: {pdf_error}")
            
            # Try to provide a meaningful error response
            error_msg = f"PDF processing failed: {str(pdf_error)}"
            
            # Check if it's a corruption issue
            if any(keyword in str(pdf_error).lower() for keyword in ['syntax error', 'xref', 'trailer', 'corrupted', 'invalid']):
                error_msg += "\n\nThis PDF appears to be corrupted or damaged. Please try:"
                error_msg += "\n1. Re-downloading the PDF from the original source"
                error_msg += "\n2. Using a PDF repair tool before uploading"
                error_msg += "\n3. Converting the PDF to images manually and uploading those instead"
            
            # Create a minimal error response
            list_of_extracted_text_strings = [error_msg]
        
        # Save raw OCR output
        raw_ocr_output = "\n".join(list_of_extracted_text_strings)
        with open(raw_ocr_output_file_path, "w") as f:
            f.write(raw_ocr_output)
        logging.info(f"Raw OCR output written to: {raw_ocr_output_file_path}")

        # Process document with LLM
        logging.info("Processing document...")
        final_text = await process_document(list_of_extracted_text_strings, reformat_as_markdown, suppress_headers_and_page_numbers)            
        cleaned_text = remove_corrected_text_header(final_text)
        
        # Save the LLM corrected output
        with open(llm_corrected_output_file_path, 'w') as f:
            f.write(cleaned_text)
        logging.info(f"LLM Corrected text written to: {llm_corrected_output_file_path}") 

        # Perform quality assessment
        quality_score, explanation = await assess_output_quality(raw_ocr_output, final_text)
        
        # Return results
        result = {
            "raw_ocr_file": raw_ocr_output_file_path,
            "processed_file": llm_corrected_output_file_path,
            "quality_score": quality_score,
            "explanation": explanation,
            "pages_processed": len(list_of_scanned_images),
            "raw_text_length": len(raw_ocr_output),
            "processed_text_length": len(cleaned_text)
        }
        
        logging.info(f"Done processing {input_pdf_file_path}.")
        logging.info(f"Quality score: {quality_score}/100" if quality_score else "Quality score: N/A")
        
        return result
        
    except Exception as e:
        logging.error(f"Error processing PDF file {input_pdf_file_path}: {e}")
        logging.error(traceback.format_exc())
        return None

async def main():
    try:
        # Suppress HTTP request logs
        logging.getLogger("httpx").setLevel(logging.WARNING)
        input_pdf_file_path = '160301289-Warren-Buffett-Katharine-Graham-Letter.pdf'
        max_test_pages = 0
        skip_first_n_pages = 0
        reformat_as_markdown = True
        suppress_headers_and_page_numbers = True
        
        # Use the new process_pdf_file function
        result = await process_pdf_file(
            input_pdf_file_path, 
            max_test_pages, 
            skip_first_n_pages, 
            reformat_as_markdown, 
            suppress_headers_and_page_numbers
        )
        
        if result:
            logging.info("\nProcessing completed successfully!")
            logging.info("See output files:")
            logging.info(f" Raw OCR: {result['raw_ocr_file']}")
            logging.info(f" LLM Corrected: {result['processed_file']}")
            if result['quality_score']:
                logging.info(f"Final quality score: {result['quality_score']}/100")
                logging.info(f"Explanation: {result['explanation']}")
        else:
            logging.error("Processing failed!")
            
    except Exception as e:
        logging.error(f"An error occurred in the main function: {e}")
        logging.error(traceback.format_exc())
        
if __name__ == '__main__':
    asyncio.run(main())
