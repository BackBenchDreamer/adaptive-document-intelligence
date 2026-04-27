# Quick Reference

Command cheat sheet and quick reference for the Adaptive Document Intelligence System.

## Common Commands

### Processing Documents

```bash
# Single document
python scripts/run_pipeline.py --image receipt.jpg

# Batch processing
python scripts/run_pipeline.py --batch --input-dir receipts/ --output results.json

# With specific OCR engine
python scripts/run_pipeline.py --image receipt.jpg --ocr-engine tesseract

# Enable preprocessing
python scripts/run_pipeline.py --image receipt.jpg --preprocess
```

### Evaluation

```bash
# Evaluate on training set
python scripts/run_evaluation.py --split train

# Evaluate with limit
python scripts/run_evaluation.py --split train --limit 100

# Save detailed report
python scripts/run_evaluation.py --split train --output evaluation.json
```

### Error Analysis

```bash
# Analyze errors
python scripts/run_error_analysis.py --split train

# Show examples
python scripts/run_error_analysis.py --split train --show-examples

# Save report
python scripts/run_error_analysis.py --split train --output errors.json
```

### Testing

```bash
# Run all tests
python tests/run_tests.py

# Run specific suite
python tests/run_tests.py unit
python tests/run_tests.py integration
python tests/run_tests.py e2e

# Run with coverage
python tests/run_tests.py coverage
```

## Python Quick Start

### Basic Usage

```python
from pipeline import DocumentProcessor

# Initialize
processor = DocumentProcessor(ocr_engine='tesseract')

# Process document
result = processor.process_document('receipt.jpg')

# Access fields
date = result['fields']['date']['value']
total = result['fields']['total']['value']
confidence = result['fields']['date']['confidence']
```

### Batch Processing

```python
from pipeline import BatchProcessor, DocumentProcessor

processor = DocumentProcessor()
batch = BatchProcessor(processor, max_workers=4, use_parallel=True)

results = batch.process_directory('receipts/', limit=100)
print(f"Processed: {len(results['results'])} documents")
```

## Configuration

### Environment Variables

```bash
export OCR_ENGINE=tesseract
export TESSERACT_CMD=/opt/homebrew/bin/tesseract
export LOG_LEVEL=INFO
export ENABLE_CACHE=true
```

### Python Configuration

```python
from core.config import Config

Config.OCR_ENGINE = 'tesseract'
Config.LOG_LEVEL = 'DEBUG'
Config.ENABLE_OCR_CACHE = True
```

## Key File Paths

```
Configuration:     core/config.py
Logging:          core/logging_config.py
OCR:              pipeline/ocr.py
Extraction:       pipeline/extractor.py
Confidence:       pipeline/confidence.py
Pipeline:         pipeline/pipeline.py
Dataset:          tests/SROIE2019/
Logs:             output/logs/
Cache:            output/cache/ocr/
```

## Troubleshooting Quick Fixes

### OCR Not Working

```bash
# Check Tesseract
which tesseract
tesseract --version

# Set path
export TESSERACT_CMD=/opt/homebrew/bin/tesseract
```

### Low Accuracy

```python
# Enable preprocessing
result = processor.process_document('receipt.jpg', preprocess=True)

# Try different engine
processor = DocumentProcessor(ocr_engine='paddleocr')
```

### Memory Issues

```python
# Process in chunks
chunk_size = 50
for i in range(0, len(files), chunk_size):
    chunk = files[i:i+chunk_size]
    results = processor.process_batch(chunk)
```

## Performance Tips

- **Enable caching**: `Config.ENABLE_OCR_CACHE = True`
- **Use Tesseract**: Faster than PaddleOCR
- **Parallel processing**: `use_parallel=True`
- **Limit batch size**: Process in chunks

## Common Patterns

### Error Handling

```python
try:
    result = processor.process_document('receipt.jpg')
    if result['metadata']['success']:
        process_result(result)
    else:
        handle_error(result['metadata']['error'])
except Exception as e:
    logger.error(f"Processing failed: {e}")
```

### Confidence Filtering

```python
MIN_CONFIDENCE = 0.7

if result['fields']['date']['confidence'] >= MIN_CONFIDENCE:
    use_date(result['fields']['date']['value'])
else:
    request_manual_review(result)
```

---

**For detailed information, see:**
- [User Guide](user_guide.md)
- [API Reference](api_reference.md)
- [FAQ](faq.md)
