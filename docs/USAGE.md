# Usage Guide

## Quick Start

### 1. Start the API server

```bash
cd backend
python main.py
```

### 2. Upload an invoice

#### Option A: Using cURL

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/invoice.jpg"
```

#### Option B: Using the test script

```bash
cd backend
python test_api.py /path/to/invoice.jpg
```

#### Option C: Using Python requests

```python
import requests

url = "http://localhost:8000/upload"
files = {'file': open('invoice.jpg', 'rb')}
response = requests.post(url, files=files)

if response.status_code == 200:
    data = response.json()
    print("Invoice Number:", data['extracted_data']['invoice_number'])
    print("Date:", data['extracted_data']['date'])
    print("Total Amount:", data['extracted_data']['total_amount'])
```

## Supported File Types

- **PNG** - `.png`
- **JPEG** - `.jpg`, `.jpeg`
- **PDF** - `.pdf`

## Extracted Fields

The API currently extracts three key fields:

### 1. Invoice Number

**Patterns recognized:**
- `INV-123`
- `INV123`
- `Invoice #123`
- `Invoice: 123`
- `Invoice Number: ABC-123`

### 2. Date

**Formats recognized:**
- `DD/MM/YYYY` (e.g., 12/03/2024)
- `DD-MM-YYYY` (e.g., 12-03-2024)
- `YYYY-MM-DD` (e.g., 2024-03-12)
- `DD Month YYYY` (e.g., 12 March 2024)

### 3. Total Amount

**Keywords recognized:**
- Total
- Amount Due
- Grand Total
- Balance Due

The system looks for amounts near these keywords and returns the highest value found.

## Example Response

```json
{
  "status": "success",
  "filename": "invoice_sample.jpg",
  "extracted_data": {
    "invoice_number": "INV-2024-001",
    "date": "15/03/2024",
    "total_amount": "2450.50"
  },
  "raw_text": "INVOICE\nInvoice Number: INV-2024-001\nDate: 15/03/2024\n..."
}
```

## Tips for Best Results

1. **Image Quality**: Use clear, high-resolution images
2. **Orientation**: Ensure the document is properly oriented
3. **Lighting**: Avoid shadows and glare
4. **Format**: Standard invoice layouts work best

## Limitations (Current Phase)

- **Simple pattern matching**: Uses regex, not ML models
- **English only**: Currently optimized for English text
- **Standard formats**: Works best with common invoice layouts
- **Three fields only**: Only extracts invoice number, date, and total amount

## Next Steps

See [ARCHITECTURE.md](ARCHITECTURE.md) for information about planned improvements and the feedback system.