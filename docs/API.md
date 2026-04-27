# API Documentation

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

**GET** `/`

Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Invoice OCR API is running",
  "version": "1.0.0"
}
```

---

### Upload Invoice

**POST** `/upload`

Upload an invoice image and extract structured data.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with file field

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file | File | Yes | Invoice image (PNG, JPG, JPEG, PDF) |

**Example Request (cURL):**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/invoice.jpg"
```

**Example Request (Python):**
```python
import requests

url = "http://localhost:8000/upload"
files = {'file': open('invoice.jpg', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

**Success Response (200):**
```json
{
  "status": "success",
  "filename": "invoice.jpg",
  "extracted_data": {
    "invoice_number": "INV-123",
    "date": "12/03/2024",
    "total_amount": "1450.00"
  },
  "raw_text": "Invoice text preview..."
}
```

**Error Response (400 - Invalid File Type):**
```json
{
  "detail": "Invalid file type. Allowed: .png, .jpg, .jpeg, .pdf"
}
```

**Error Response (500 - Processing Failed):**
```json
{
  "detail": "Processing failed: [error message]"
}
```

---

## Interactive Documentation

Once the server is running, you can access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- View all endpoints
- See request/response schemas
- Test the API directly from your browser