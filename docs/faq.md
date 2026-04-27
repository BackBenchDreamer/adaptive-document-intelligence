# Frequently Asked Questions (FAQ)

Common questions and answers about the Adaptive Document Intelligence System.

## General Questions

### What is this system?

The Adaptive Document Intelligence System is a production-grade document processing pipeline that extracts structured data from financial documents (receipts and invoices) using OCR and heuristic-based field extraction.

### Who is this system for?

- Developers building document processing applications
- Businesses automating receipt/invoice processing
- Researchers studying document intelligence
- Anyone needing to extract data from financial documents

### What documents does it support?

Currently supports:
- Receipts
- Invoices
- Financial documents with date, total, and invoice number fields

### Is it production-ready?

Yes! The system includes:
- Robust error handling
- Comprehensive logging
- Performance monitoring
- Extensive testing (65+ tests)
- Complete documentation

## Installation Questions

### What are the system requirements?

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- ~3GB disk space
- macOS, Linux, or Windows

### Do I need both OCR engines?

No, you only need one:
- **Tesseract**: Faster, easier to install (recommended for most users)
- **PaddleOCR**: Higher accuracy, requires more resources

### How do I install Tesseract?

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Installation fails with "No module named 'paddleocr'"

PaddleOCR is optional. Either:
1. Install it: `pip install paddleocr paddlepaddle`
2. Use Tesseract instead: `Config.OCR_ENGINE = 'tesseract'`

## Usage Questions

### How do I process a single document?

```python
from pipeline import DocumentProcessor

processor = DocumentProcessor()
result = processor.process_document('receipt.jpg')
print(result['fields']['total']['value'])
```

### How do I process multiple documents?

```python
from pipeline import BatchProcessor, DocumentProcessor

processor = DocumentProcessor()
batch = BatchProcessor(processor, use_parallel=True)
results = batch.process_directory('receipts/')
```

### What image formats are supported?

- JPG/JPEG
- PNG
- Other formats supported by PIL/Pillow

### What's the recommended image quality?

- **Resolution**: 300 DPI or higher
- **Size**: 1024x768 pixels minimum
- **Quality**: Clear, well-lit, straight orientation

### How do I improve accuracy?

1. **Use better images**: Higher resolution, good lighting
2. **Enable preprocessing**: `preprocess=True`
3. **Try PaddleOCR**: More accurate than Tesseract
4. **Check confidence scores**: Review low-confidence extractions

### What do confidence scores mean?

- **0.9-1.0**: High confidence - Very reliable
- **0.7-0.9**: Good confidence - Generally reliable
- **0.5-0.7**: Medium confidence - Review recommended
- **0.0-0.5**: Low confidence - Manual verification needed

## Performance Questions

### How fast is the system?

- **Tesseract**: ~0.8s per document
- **PaddleOCR**: ~2-3s per document
- **With cache**: <0.1s per document (cached)

### How can I speed up processing?

1. **Enable caching**: `Config.ENABLE_OCR_CACHE = True`
2. **Use Tesseract**: Faster than PaddleOCR
3. **Parallel processing**: `use_parallel=True`
4. **Process in chunks**: Avoid memory issues

### Why is processing slow?

Common causes:
- Large images (resize before processing)
- PaddleOCR on CPU (use Tesseract or enable GPU)
- No caching enabled
- Sequential processing (enable parallel)

### How much memory does it use?

- **Per document**: ~100-200MB
- **Batch processing**: Depends on batch size
- **PaddleOCR**: ~2GB for models

### Can I use GPU acceleration?

Yes, with PaddleOCR:
```python
from core.config import Config
Config.PADDLEOCR_USE_GPU = True
```

Requires CUDA-compatible GPU and paddlepaddle-gpu.

## Accuracy Questions

### What's the expected accuracy?

Based on SROIE2019 dataset:
- **Date**: 85-90%
- **Total**: 80-85%
- **Overall**: 82-87%

### Why is accuracy lower than expected?

Common reasons:
- Poor image quality
- Non-standard document formats
- OCR errors
- Unusual date/number formats

### How do I handle extraction errors?

```python
result = processor.process_document('receipt.jpg')

if result['fields']['date']['confidence'] < 0.7:
    # Request manual review
    request_manual_review(result)
else:
    # Use extracted value
    process_date(result['fields']['date']['value'])
```

### Can I train the system on my documents?

The system uses heuristic-based extraction (not ML), so no training is needed. However, you can:
1. Adjust extraction patterns
2. Add custom extractors
3. Calibrate confidence scores with validation data

## Troubleshooting

### OCR returns empty text

**Causes:**
- Tesseract not installed/configured
- Image file not found
- Unsupported image format

**Solutions:**
```bash
# Check Tesseract
which tesseract
tesseract --version

# Set path
export TESSERACT_CMD=/opt/homebrew/bin/tesseract

# Try preprocessing
result = processor.process_document('image.jpg', preprocess=True)
```

### Extraction returns None

**Causes:**
- No matching patterns found
- OCR text quality too low
- Unusual document format

**Solutions:**
1. Check OCR output quality
2. Enable preprocessing
3. Try different OCR engine
4. Review extraction patterns

### "Permission denied" errors

**Solution:**
```bash
# Create directories with proper permissions
mkdir -p output/logs output/cache/ocr
chmod 755 output output/logs output/cache output/cache/ocr
```

### Memory errors

**Solutions:**
```python
# Process in smaller batches
chunk_size = 50
for chunk in chunks(files, chunk_size):
    results = processor.process_batch(chunk)
    save_results(results)
    del results  # Free memory
```

### Import errors

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Development Questions

### How do I add a new field extractor?

See [Development Guide](development.md#adding-new-field-extractors) for detailed instructions.

Basic steps:
1. Create extractor class inheriting from `FieldExtractor`
2. Implement `extract()` method
3. Add to `ExtractionManager`
4. Write tests

### How do I add a new OCR engine?

See [Development Guide](development.md#adding-a-new-ocr-engine) for detailed instructions.

Basic steps:
1. Create engine class inheriting from `OCREngine`
2. Implement `extract_text()` and `is_available()`
3. Register in `OCRManager`
4. Write tests

### How do I run tests?

```bash
# All tests
python tests/run_tests.py

# Specific suite
python tests/run_tests.py unit

# With coverage
python tests/run_tests.py coverage
```

### How do I contribute?

See [Development Guide](development.md#contributing) for:
- Development setup
- Coding standards
- Pull request process
- Code review guidelines

## Configuration Questions

### Where is configuration stored?

- **Code**: `core/config.py`
- **Environment**: `.env` file or environment variables
- **Runtime**: Can be modified in code

### How do I change OCR engine?

```python
from core.config import Config
Config.OCR_ENGINE = 'tesseract'  # or 'paddleocr'
```

Or via environment:
```bash
export OCR_ENGINE=tesseract
```

### How do I enable debug logging?

```python
from core.config import Config
Config.LOG_LEVEL = 'DEBUG'
```

Or via environment:
```bash
export LOG_LEVEL=DEBUG
```

### Where are logs stored?

Default location: `output/logs/adi_system.log`

Configure via:
```python
Config.LOG_FILE_PATH = Path('custom/path/to/log.log')
```

## Dataset Questions

### What is SROIE2019?

SROIE2019 (Scanned Receipts OCR and Information Extraction) is a public dataset of receipt images with ground truth annotations used for evaluation.

### Do I need the dataset?

No, the dataset is only needed for:
- Running evaluations
- Testing the system
- Benchmarking performance

### How do I use my own documents?

Just provide image paths:
```python
result = processor.process_document('my_receipt.jpg')
```

No dataset required for processing your own documents.

## Deployment Questions

### Can I deploy this as an API?

Yes! The system can be wrapped in a REST API using Flask/FastAPI:

```python
from flask import Flask, request
from pipeline import DocumentProcessor

app = Flask(__name__)
processor = DocumentProcessor()

@app.route('/process', methods=['POST'])
def process():
    file = request.files['image']
    result = processor.process_document(file)
    return result
```

### Can I use Docker?

Yes, create a Dockerfile:
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y tesseract-ocr
COPY . .
CMD ["python", "app.py"]
```

### Is it scalable?

Current design is single-machine. For scale:
- Use message queues (Celery, RabbitMQ)
- Distribute processing across workers
- Use Redis for caching
- Deploy multiple instances behind load balancer

## Still Have Questions?

- Check [User Guide](user_guide.md) for usage details
- Check [API Reference](api_reference.md) for API documentation
- Check [Development Guide](development.md) for development info
- Create an issue on GitHub
- Review existing issues and discussions

---

**Can't find your question?** Create an issue and we'll add it to the FAQ!
