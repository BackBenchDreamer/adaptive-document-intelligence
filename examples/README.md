# Example Invoices

This directory contains sample invoices for testing the OCR extraction system.

## Sample Invoice

**File:** `sample_invoice.txt`

A text-based invoice that can be converted to an image for testing.

**Expected Extraction:**
- **Invoice Number:** INV-2024-001
- **Date:** 15/03/2024
- **Total Amount:** 8424.00

## Creating Test Images

### Option 1: Screenshot
1. Open `sample_invoice.txt` in a text editor
2. Take a screenshot
3. Save as PNG or JPG

### Option 2: Convert to PDF (macOS/Linux)
```bash
# Using enscript and ps2pdf
enscript sample_invoice.txt -o - | ps2pdf - sample_invoice.pdf
```

### Option 3: Use Online Tools
- Copy the text from `sample_invoice.txt`
- Paste into a document editor (Google Docs, Word)
- Export as PDF or save as image

## Testing the API

Once you have an image:

```bash
# Start the server
cd backend
python main.py

# In another terminal, test the upload
curl -X POST "http://localhost:8000/upload" \
  -F "file=@sample_invoice.png"

# Or use the test script
python test_api.py ../examples/sample_invoice.png
```

## Adding Your Own Invoices

Feel free to add your own invoice samples to this directory for testing. The system works best with:

- Clear, high-resolution images
- Standard invoice layouts
- English text
- Common date formats (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD)
- Invoice numbers with patterns like INV-123, Invoice #123