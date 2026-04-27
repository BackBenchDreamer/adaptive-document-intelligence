from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image
import re
import os
import tempfile
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Invoice OCR API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from image using Tesseract OCR
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text as a single string
    """
    try:
        # Open image with PIL
        image = Image.open(image_path)
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(image)
        
        logger.info(f"Extracted text length: {len(text)} characters")
        return text
    
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


def extract_invoice_fields(text: str) -> Dict[str, Optional[str]]:
    """
    Extract invoice fields using regex and simple heuristics
    
    Args:
        text: Raw text extracted from OCR
        
    Returns:
        Dictionary with extracted fields
    """
    result = {
        "invoice_number": None,
        "date": None,
        "total_amount": None
    }
    
    # Extract invoice number
    # Patterns: INV-123, INV123, Invoice #123, etc.
    invoice_patterns = [
        r"INV[-#]?\d+",
        r"Invoice\s*[#:]?\s*(\d+)",
        r"Invoice\s*Number\s*[#:]?\s*([\w-]+)",
    ]
    
    for pattern in invoice_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result["invoice_number"] = matches[0] if isinstance(matches[0], str) else matches[0]
            break
    
    # Extract date
    # Patterns: DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY, YYYY-MM-DD
    date_patterns = [
        r"\d{2}/\d{2}/\d{4}",
        r"\d{2}-\d{2}-\d{4}",
        r"\d{4}-\d{2}-\d{2}",
        r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}",
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result["date"] = matches[0]
            break
    
    # Extract total amount
    # Look for amounts with currency symbols or keywords like "Total", "Amount Due"
    amount_patterns = [
        r"Total\s*[:\$]?\s*(\d+[,\.]?\d*\.?\d{2})",
        r"Amount\s*Due\s*[:\$]?\s*(\d+[,\.]?\d*\.?\d{2})",
        r"Grand\s*Total\s*[:\$]?\s*(\d+[,\.]?\d*\.?\d{2})",
        r"\$\s*(\d+[,\.]?\d*\.?\d{2})",
    ]
    
    amounts = []
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Clean and convert to float
            for match in matches:
                cleaned = match.replace(",", "")
                try:
                    amounts.append(float(cleaned))
                except ValueError:
                    continue
    
    # If no specific total found, find all amounts and take the maximum
    if not amounts:
        all_amounts = re.findall(r"\d+[,\.]?\d*\.?\d{2}", text)
        for amount in all_amounts:
            cleaned = amount.replace(",", "")
            try:
                amounts.append(float(cleaned))
            except ValueError:
                continue
    
    if amounts:
        result["total_amount"] = f"{max(amounts):.2f}"
    
    logger.info(f"Extracted fields: {result}")
    return result


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Invoice OCR API is running",
        "version": "1.0.0"
    }


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Upload an invoice image and extract structured data
    
    Args:
        file: Invoice image file (PNG, JPG, JPEG, PDF)
        
    Returns:
        JSON with extracted invoice fields
    """
    # Validate file type
    allowed_extensions = {".png", ".jpg", ".jpeg", ".pdf"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file to temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        logger.info(f"Processing file: {file.filename}")
        
        # Step 1: Extract text using OCR
        extracted_text = extract_text_from_image(temp_path)
        
        # Step 2: Extract structured fields
        extracted_fields = extract_invoice_fields(extracted_text)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "extracted_data": extracted_fields,
            "raw_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
        }
    
    except Exception as e:
        # Clean up on error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
