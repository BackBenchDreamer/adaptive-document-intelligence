# Setup Guide

## Prerequisites

- Python 3.8+ (Python 3.14+ recommended)
- pip

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd adaptive-document-intelligence
```

### 2. Create a virtual environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Tesseract OCR Engine

Tesseract is required for OCR functionality.

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

**Verify installation:**
```bash
tesseract --version
```

### 4. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note:** Installation takes 1-2 minutes.

## Running the API

### Start the server

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

### Verify it's running

```bash
curl http://localhost:8000
```

Expected response:
```json
{
  "status": "ok",
  "message": "Invoice OCR API is running",
  "version": "1.0.0"
}
```

## Troubleshooting

### Tesseract not found

If you get "tesseract is not installed" error:

1. Make sure Tesseract is installed (see step 3 above)
2. Verify with: `tesseract --version`
3. On macOS, if Homebrew installation fails, try:
   ```bash
   brew update
   brew install tesseract
   ```
4. On Windows, make sure Tesseract is in your PATH

### Python version issues

If you encounter Python compatibility issues:

1. Make sure you have Python 3.8 or higher
2. Check with: `python3 --version`
3. Consider using Python 3.11 or 3.12 for best compatibility

### Port already in use

If port 8000 is already in use, you can change it in `backend/main.py`:

```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change to any available port