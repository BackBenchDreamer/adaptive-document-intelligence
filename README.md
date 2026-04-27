# Adaptive Document Intelligence System

Production-grade AI pipeline for extracting structured data from financial documents with feedback-driven learning.

## Problem Statement

Manual extraction of financial documents (invoices, payslips) is error-prone and time-consuming.

Most existing solutions:
- Are static
- Do not improve over time
- Lack system-level reliability

This project builds a self-improving pipeline with feedback loops and production-grade architecture.

## Architecture

```
Upload → OCR → Extraction → JSON Output → Feedback → Dataset
```

*(Detailed architecture diagram coming soon)*

## Features

- **OCR-based text extraction** - Extract text from document images
- **Rule-based + NLP field extraction** - Identify key fields using patterns and NLP
- **Confidence scoring** - Track extraction reliability
- **Feedback collection system** - Learn from corrections
- **Async-ready architecture** - Designed for scalability (planned)

## Tech Stack

- **FastAPI** - Modern web framework
- **Tesseract OCR** - OCR engine
- **Regex** - Text processing and pattern matching
- **PostgreSQL** - Database (planned)
- **Redis + Celery** - Task queue (planned)
- **Docker** - Containerization (planned)

## Roadmap

- [ ] Basic OCR pipeline
- [ ] Field extraction (invoice number, date, total)
- [ ] Async processing
- [ ] Feedback system
- [ ] Retry + logging
- [ ] Production deployment

## Getting Started

### Quick Setup

**macOS/Linux:**
```bash
# 1. Clone and navigate
git clone <repository-url>
cd adaptive-document-intelligence

# 2. Install Tesseract OCR
brew install tesseract  # macOS
# sudo apt-get install tesseract-ocr  # Ubuntu/Debian

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
cd backend
pip install -r requirements.txt

# 5. Run the server
python main.py
```

**Windows:**
```bash
# 1. Clone and navigate
git clone <repository-url>
cd adaptive-document-intelligence

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Run the server
python main.py
```

### Quick Test

```bash
# Upload an invoice
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/invoice.jpg"
```

**Response:**
```json
{
  "status": "success",
  "extracted_data": {
    "invoice_number": "INV-123",
    "date": "12/03/2024",
    "total_amount": "1450.00"
  }
}
```

## Documentation

- **[Setup Guide](docs/SETUP.md)** - Installation and configuration
- **[API Reference](docs/API.md)** - Endpoint documentation
- **[Usage Guide](docs/USAGE.md)** - Examples and best practices
- **[Architecture](docs/ARCHITECTURE.md)** - System design and decisions

## Current Status

✅ **Phase 1 Complete** - Basic OCR Pipeline
- FastAPI endpoint working
- Tesseract OCR integration
- Regex-based field extraction
- JSON output
- Python 3.14+ compatible

🚧 **Next Steps**
- Feedback collection system
- ML model integration
- Async processing
- Production deployment

## License

See [LICENSE](LICENSE) file for details.
