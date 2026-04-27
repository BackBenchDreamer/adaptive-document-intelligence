# User Guide

Complete guide to using the Adaptive Document Intelligence System.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Processing Documents](#processing-documents)
3. [Understanding Results](#understanding-results)
4. [Configuration Options](#configuration-options)
5. [Command Line Tools](#command-line-tools)
6. [Best Practices](#best-practices)
7. [Common Use Cases](#common-use-cases)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### First Steps

After installation, verify your setup:

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Verify installation
python -c "from core.config import Config; print(Config.get_config_summary())"
```

### Your First Document

Process a single receipt:

```python
from pipeline.pipeline import DocumentProcessor

# Initialize processor
processor = DocumentProcessor()

# Process document
result = processor.process_document('receipt.jpg')

# Print results
print(f"Date: {result['fields']['date']['value']}")
print(f"Total: {result['fields']['total']['value']}")
print(f"Confidence: {result['fields']['date']['confidence']:.2f}")
```

## Processing Documents

### Single Document Processing

#### Using Python API

```python
from pipeline.pipeline import DocumentProcessor

# Initialize with default settings
processor = DocumentProcessor()

# Process document
result = processor.process_document('path/to/receipt.jpg')

# Access extracted fields
date = result['fields']['date']['value']
total = result['fields']['total']['value']
invoice_number = result['fields'].get('invoice_number', {}).get('value')

# Check confidence scores
date_confidence = result['fields']['date']['confidence']
total_confidence = result['fields']['total']['confidence']

print(f"Date: {date} (confidence: {date_confidence:.2f})")
print(f"Total: {total} (confidence: {total_confidence:.2f})")
```

#### Using Command Line

```bash
# Process single document
python scripts/run_pipeline.py --image receipt.jpg

# With detailed output
python scripts/run_pipeline.py --image receipt.jpg --verbose

# Save results to file
python scripts/run_pipeline.py --image receipt.jpg --output result.json
```

### Batch Processing

#### Using Python API

```python
from pipeline.pipeline import DocumentProcessor
from pathlib import Path

# Initialize processor
processor = DocumentProcessor()

# Get list of images
image_paths = list(Path('receipts/').glob('*.jpg'))

# Process batch
results = processor.process_batch(
    image_paths=image_paths,
    max_workers=4  # Parallel processing
)

# Analyze results
successful = sum(1 for r in results if r.get('success', False))
print(f"Processed: {successful}/{len(results)} documents")

# Get failed documents
failed = [r for r in results if not r.get('success', False)]
for doc in failed:
    print(f"Failed: {doc['image_path']} - {doc.get('error', 'Unknown error')}")
```

#### Using Command Line

```bash
# Process all images in directory
python scripts/run_pipeline.py --batch --input-dir receipts/

# Limit number of documents
python scripts/run_pipeline.py --batch --input-dir receipts/ --limit 100

# Save results
python scripts/run_pipeline.py --batch --input-dir receipts/ --output results.json

# Parallel processing
python scripts/run_pipeline.py --batch --input-dir receipts/ --workers 4
```

### Advanced Processing Options

#### Custom OCR Engine

```python
from pipeline.pipeline import DocumentProcessor

# Use specific OCR engine
processor = DocumentProcessor(ocr_engine='tesseract')

# Or configure globally
from core.config import Config
Config.OCR_ENGINE = 'paddleocr'
processor = DocumentProcessor()
```

#### Image Preprocessing

```python
# Enable preprocessing for poor quality images
result = processor.process_document(
    'noisy_receipt.jpg',
    preprocess=True
)

# Preprocessing includes:
# - Grayscale conversion
# - Noise reduction
# - Contrast enhancement
# - Binarization
```

#### Confidence Thresholds

```python
# Set minimum confidence threshold
processor = DocumentProcessor(min_confidence=0.7)

# Or check confidence after processing
result = processor.process_document('receipt.jpg')

if result['date']['confidence'] < 0.7:
    print("Warning: Low confidence date extraction")
    # Handle low confidence case
```

## Understanding Results

### Result Structure

```python
result = {
    'image_path': 'receipt.jpg',
    'ocr': {
        'text': 'Receipt text...',
        'confidence': 0.9,
        'engine': 'tesseract',
        'processing_time': 0.5
    },
    'fields': {
        'date': {
            'value': '2024-01-15',
            'confidence': 0.92,
            'extraction_confidence': 0.88,
            'factors': {
                'extraction': 0.88,
                'ocr_quality': 0.90,
                'value_validity': 0.95,
                'pattern_strength': 0.85
            }
        },
        'total': {
            'value': 25.80,
            'confidence': 0.88,
            'extraction_confidence': 0.85,
            'factors': {...}
        },
        'invoice_number': {
            'value': 'INV-2024-001',
            'confidence': 0.75,
            'extraction_confidence': 0.72,
            'factors': {...}
        }
    },
    'overall_confidence': 0.85,
    'processing_time': 0.85,
    'timestamp': '2024-01-27T10:30:00Z'
}
```

### Confidence Scores

Confidence scores range from 0.0 to 1.0:

- **0.9 - 1.0**: High confidence - Very reliable
- **0.7 - 0.9**: Good confidence - Generally reliable
- **0.5 - 0.7**: Medium confidence - Review recommended
- **0.0 - 0.5**: Low confidence - Manual verification needed

**Factors affecting confidence:**
- OCR quality
- Pattern match strength
- Contextual validation
- Format consistency

### Handling Missing Fields

```python
result = processor.process_document('receipt.jpg')

# Safe access with defaults
date = result.get('fields', {}).get('date', {}).get('value', 'Not found')
total = result.get('fields', {}).get('total', {}).get('value', 0.0)

# Check if field was extracted
if 'invoice_number' in result.get('fields', {}) and result['fields']['invoice_number']['value']:
    print(f"Invoice: {result['fields']['invoice_number']['value']}")
else:
    print("Invoice number not found")

# Check confidence before using
if result['fields']['date']['confidence'] > 0.7:
    # Use the date
    process_date(result['fields']['date']['value'])
else:
    # Request manual verification
    request_manual_review(result)
```

## Configuration Options

### Environment Variables

```bash
# OCR Configuration
export OCR_ENGINE=tesseract              # or paddleocr
export TESSERACT_CMD=/usr/bin/tesseract
export PADDLEOCR_USE_GPU=false

# Processing Configuration
export ENABLE_CACHE=true
export CACHE_DIR=output/cache/ocr
export MAX_WORKERS=4

# Logging Configuration
export LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
export LOG_FORMAT_JSON=true
export LOG_FILE=output/logs/adi_system.log

# Dataset Configuration
export DATASET_PATH=tests/SROIE2019
```

### Python Configuration

```python
from core.config import Config

# OCR Settings
Config.OCR_ENGINE = 'tesseract'
Config.TESSERACT_CMD = '/opt/homebrew/bin/tesseract'
Config.PADDLEOCR_USE_GPU = False

# Cache Settings
Config.ENABLE_CACHE = True
Config.CACHE_DIR = Path('output/cache/ocr')

# Logging Settings
Config.LOG_LEVEL = 'INFO'
Config.LOG_FORMAT_JSON = True

# Processing Settings
Config.MAX_WORKERS = 4
Config.BATCH_SIZE = 100
```

### Configuration File

Create `.env` file in project root:

```bash
# .env file
OCR_ENGINE=tesseract
ENABLE_CACHE=true
LOG_LEVEL=INFO
MAX_WORKERS=4
```

Load configuration:

```python
from dotenv import load_dotenv
load_dotenv()

from pipeline.pipeline import DocumentProcessor
processor = DocumentProcessor()
```

## Command Line Tools

### run_pipeline.py

Main processing script:

```bash
# Single document
python scripts/run_pipeline.py --image receipt.jpg

# Batch processing
python scripts/run_pipeline.py --batch --input-dir receipts/

# With options
python scripts/run_pipeline.py \
    --batch \
    --input-dir receipts/ \
    --output results.json \
    --workers 4 \
    --limit 100 \
    --verbose
```

**Options:**
- `--image PATH`: Process single image
- `--batch`: Enable batch processing
- `--input-dir DIR`: Input directory for batch
- `--output FILE`: Output JSON file
- `--workers N`: Number of parallel workers
- `--limit N`: Maximum documents to process
- `--verbose`: Detailed output
- `--preprocess`: Enable image preprocessing

### run_evaluation.py

Evaluate system performance:

```bash
# Evaluate on training set
python scripts/run_evaluation.py --split train

# Evaluate on test set
python scripts/run_evaluation.py --split test

# Limit evaluation
python scripts/run_evaluation.py --split train --limit 100

# Save detailed report
python scripts/run_evaluation.py --split train --output evaluation_report.json
```

**Output:**
```
=== Evaluation Results ===
Date Extraction:
  Accuracy: 87.5%
  Precision: 0.89
  Recall: 0.86
  F1 Score: 0.87

Total Extraction:
  Accuracy: 83.2%
  Precision: 0.85
  Recall: 0.81
  F1 Score: 0.83

Overall Accuracy: 85.4%
Processing Time: 0.82s per document
```

### run_error_analysis.py

Analyze extraction errors:

```bash
# Analyze errors
python scripts/run_error_analysis.py --split train

# Show example errors
python scripts/run_error_analysis.py --split train --show-examples

# Save error report
python scripts/run_error_analysis.py --split train --output error_report.json
```

**Output:**
```
=== Error Analysis ===
Total Errors: 87 / 626 (13.9%)

Error Categories:
  OCR Errors: 45 (51.7%)
  Format Errors: 28 (32.2%)
  Missing Fields: 14 (16.1%)

Common Issues:
  - Poor image quality
  - Non-standard date formats
  - Ambiguous total amounts
```

### inspect_dataset.py

Inspect dataset:

```bash
# Show statistics
python scripts/inspect_dataset.py --split train --samples 0

# Show sample documents
python scripts/inspect_dataset.py --split train --samples 5

# Show problematic documents
python scripts/inspect_dataset.py --split train --show-problematic
```

## Best Practices

### Image Quality

**Recommended:**
- Resolution: 300 DPI or higher
- Format: JPG or PNG
- Size: 1024x768 minimum
- Clear, well-lit images
- Straight orientation

**Avoid:**
- Blurry or out-of-focus images
- Low resolution (<200 DPI)
- Heavy shadows or glare
- Rotated or skewed images
- Partial or cropped receipts

### Preprocessing

Use preprocessing for:
- Low quality images
- Poor lighting
- Noisy backgrounds
- Faded text

```python
# Enable preprocessing
result = processor.process_document('poor_quality.jpg', preprocess=True)
```

### Confidence Thresholds

Set appropriate thresholds based on use case:

**High Accuracy Required (Financial):**
```python
MIN_CONFIDENCE = 0.85
if result['total']['confidence'] < MIN_CONFIDENCE:
    request_manual_review(result)
```

**Moderate Accuracy (Logging):**
```python
MIN_CONFIDENCE = 0.70
if result['date']['confidence'] < MIN_CONFIDENCE:
    log_warning(result)
```

### Error Handling

Always handle errors gracefully:

```python
from pipeline.pipeline import DocumentProcessor

processor = DocumentProcessor()

try:
    result = processor.process_document('receipt.jpg')
    
    # Check for successful extraction
    if result.get('fields'):
        process_result(result)
    else:
        handle_extraction_failure(result)
        
except FileNotFoundError:
    print("Image file not found")
except Exception as e:
    print(f"Processing error: {e}")
    log_error(e)
```

### Batch Processing

For large batches:

```python
from pipeline.pipeline import DocumentProcessor

# Initialize processor
processor = DocumentProcessor()

# Process in chunks
chunk_size = 100
for i in range(0, len(files), chunk_size):
    chunk = files[i:i+chunk_size]
    results = processor.process_batch(chunk, max_workers=4)
    save_results(results)
```

### Caching

Enable caching for repeated processing:

```python
from core.config import Config

# Enable cache
Config.ENABLE_CACHE = True
Config.CACHE_DIR = Path('output/cache/ocr')

# Cache is automatically used
processor = DocumentProcessor()
result = processor.process_document('receipt.jpg')  # Cached after first run
```

## Common Use Cases

### Use Case 1: Receipt Processing System

```python
from pipeline.pipeline import DocumentProcessor
from pathlib import Path
import json

def process_receipt_batch(receipt_dir, output_file):
    """Process receipts and save to database."""
    processor = DocumentProcessor()
    results = []
    
    for receipt_file in Path(receipt_dir).glob('*.jpg'):
        try:
            result = processor.process_document(str(receipt_file))
            
            # Validate confidence
            if result['fields']['date']['confidence'] > 0.8 and \
               result['fields']['total']['confidence'] > 0.8:
                # Save to database
                save_to_database(result)
                results.append({'file': receipt_file.name, 'status': 'success'})
            else:
                # Queue for manual review
                queue_for_review(receipt_file, result)
                results.append({'file': receipt_file.name, 'status': 'review'})
                
        except Exception as e:
            results.append({'file': receipt_file.name, 'status': 'error', 'error': str(e)})
    
    # Save summary
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results
```

### Use Case 2: Invoice Validation

```python
def validate_invoice(invoice_path, expected_total):
    """Validate invoice against expected total."""
    from pipeline.pipeline import DocumentProcessor
    
    processor = DocumentProcessor()
    result = processor.process_document(invoice_path)
    
    extracted_total = result['fields']['total']['value']
    confidence = result['fields']['total']['confidence']
    
    # Check if extraction is reliable
    if confidence < 0.85:
        return {'status': 'manual_review', 'reason': 'low_confidence'}
    
    # Validate total
    tolerance = 0.01  # $0.01 tolerance
    if abs(extracted_total - expected_total) <= tolerance:
        return {'status': 'valid', 'extracted': extracted_total}
    else:
        return {
            'status': 'mismatch',
            'expected': expected_total,
            'extracted': extracted_total,
            'difference': abs(extracted_total - expected_total)
        }
```

### Use Case 3: Expense Report Automation

```python
def generate_expense_report(receipts_dir, employee_id):
    """Generate expense report from receipts."""
    from pipeline.pipeline import DocumentProcessor
    from pathlib import Path
    
    processor = DocumentProcessor()
    expenses = []
    
    for receipt in Path(receipts_dir).glob('*.jpg'):
        result = processor.process_document(str(receipt))
        
        if result['fields']['date']['confidence'] > 0.7 and \
           result['fields']['total']['confidence'] > 0.7:
            expenses.append({
                'date': result['fields']['date']['value'],
                'amount': result['fields']['total']['value'],
                'receipt': receipt.name,
                'confidence': min(
                    result['fields']['date']['confidence'],
                    result['fields']['total']['confidence']
                )
            })
    
    # Sort by date
    expenses.sort(key=lambda x: x['date'])
    
    # Generate report
    report = {
        'employee_id': employee_id,
        'period': f"{expenses[0]['date']} to {expenses[-1]['date']}",
        'total_expenses': sum(e['amount'] for e in expenses),
        'expense_count': len(expenses),
        'expenses': expenses
    }
    
    return report
```

## Troubleshooting

### Low Accuracy

**Problem:** Extraction accuracy below 70%

**Solutions:**
1. Check image quality
2. Enable preprocessing
3. Try different OCR engine
4. Adjust confidence thresholds

```python
# Try preprocessing
result = processor.process_document('receipt.jpg', preprocess=True)

# Try different engine
from pipeline.pipeline import DocumentProcessor
processor = DocumentProcessor(ocr_engine='paddleocr')
```

### Slow Processing

**Problem:** Processing takes >5s per document

**Solutions:**
1. Use Tesseract instead of PaddleOCR
2. Enable caching
3. Use parallel processing
4. Reduce image size

```python
# Use faster engine
Config.OCR_ENGINE = 'tesseract'

# Enable caching
Config.ENABLE_CACHE = True

# Parallel processing
from pipeline.pipeline import DocumentProcessor
processor = DocumentProcessor()
results = processor.process_batch(image_paths, max_workers=4)
```

### Memory Issues

**Problem:** Out of memory errors

**Solutions:**
1. Process in smaller batches
2. Disable caching
3. Use Tesseract
4. Reduce image resolution

```python
# Process in chunks
chunk_size = 10
for chunk in chunks(files, chunk_size):
    results = processor.process_batch(chunk)
    save_results(results)
    del results  # Free memory
```

### Incorrect Extractions

**Problem:** Wrong values extracted

**Solutions:**
1. Check OCR quality
2. Review extraction patterns
3. Adjust confidence thresholds
4. Use manual review for low confidence

```python
# Check OCR output
from pipeline.ocr import OCRManager
ocr = OCRManager()
ocr_result = ocr.extract_text('receipt.jpg')
print(ocr_result['text'])  # Review OCR quality

# Set higher confidence threshold
if result['date']['confidence'] < 0.85:
    request_manual_review(result)
```

## Next Steps

- Review [API Reference](api_reference.md) for detailed API documentation
- Check [Examples](../examples/) for more code samples
- See [Development Guide](development.md) for customization
- Read [FAQ](faq.md) for common questions

---

**Need Help?**

- Check [FAQ](faq.md)
- Review [Troubleshooting](#troubleshooting)
- Check system logs in `output/logs/`
- Create an issue with details