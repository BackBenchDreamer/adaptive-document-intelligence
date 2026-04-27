# Setup Guide

## Prerequisites

- Python 3.8+
- pip

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd adaptive-document-intelligence
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note:** First-time installation may take a few minutes as PaddleOCR downloads its models.

### Platform-Specific PaddlePaddle Installation

PaddleOCR will automatically install PaddlePaddle. However, if you encounter issues:

**macOS (Apple Silicon M1/M2/M3):**
```bash
pip install paddlepaddle
```

**macOS (Intel):**
```bash
pip install paddlepaddle
```

**Linux:**
```bash
pip install paddlepaddle
```

**Windows:**
```bash
pip install paddlepaddle
```

For GPU support or specific versions, see [PaddlePaddle Installation Guide](https://www.paddlepaddle.org.cn/en/install/quick).

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

### PaddleOCR installation issues

If you encounter issues with PaddleOCR:

1. Make sure you have the correct Python version (3.8+)
2. Try installing PaddlePaddle separately first:
   ```bash
   pip install paddlepaddle
   ```
3. Then install PaddleOCR:
   ```bash
   pip install paddleocr
   ```

### Port already in use

If port 8000 is already in use, you can change it in `backend/main.py`:

```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change to any available port