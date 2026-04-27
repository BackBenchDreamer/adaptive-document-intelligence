# Examples

This directory contains usage examples for the Adaptive Document Intelligence System.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)

Demonstrates how to process a single document and extract structured fields.

**Features:**
- Initialize DocumentProcessor
- Process single image
- Access extracted fields (date, total, invoice_number)
- Check confidence scores

**Usage:**
```bash
python examples/basic_usage.py
```

### 2. Batch Processing (`batch_processing.py`)

Demonstrates how to process multiple documents efficiently.

**Features:**
- Process directory of images
- Calculate batch statistics
- Track success/failure rates
- Save results to JSON

**Usage:**
```bash
python examples/batch_processing.py
```

### 3. Custom Extraction (`custom_extraction.py`)

Demonstrates how to use individual extractors for custom workflows.

**Features:**
- Use DateExtractor, TotalExtractor, InvoiceNumberExtractor directly
- Access extraction candidates
- Understand extraction methods
- Custom extraction logic

**Usage:**
```bash
python examples/custom_extraction.py
```

## Running Examples

### Prerequisites

1. Install the system:
```bash
pip install -r requirements.txt
```

2. Ensure Tesseract OCR is installed:
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Modify Examples

Before running, update the image paths in each example:

**basic_usage.py:**
```python
result = processor.process_document('path/to/your/receipt.jpg')
```

**batch_processing.py:**
```python
image_dir = Path('path/to/your/receipts/')
```

**custom_extraction.py:**
```python
# Uses hardcoded sample text - no changes needed
```

## Expected Output

### Basic Usage
```
Processing document...

=== Extraction Results ===
Date: 2024-01-15 (confidence: 0.92)
Total: $25.80 (confidence: 0.88)
Invoice: INV-2024-001 (confidence: 0.75)

Processing time: 0.85s
OCR engine: tesseract
```

### Batch Processing
```
Processing batch...
Processing: 100%|████████████| 100/100 [01:25<00:00,  1.17it/s]

=== Batch Statistics ===
Total processed: 100
Successful: 95
Failed: 5
Avg processing time: 0.85s

=== Field Statistics ===
date:
  Avg confidence: 0.87
  Extraction rate: 95.0%
total:
  Avg confidence: 0.83
  Extraction rate: 92.0%
invoice_number:
  Avg confidence: 0.78
  Extraction rate: 88.0%

Results saved to batch_results.json
```

### Custom Extraction
```
Extracting fields...

=== Extraction Results ===
Date: 2024-01-15 (confidence: 0.92)
  Method: date_pattern_ddmmyyyy
  Candidates: 1

Total: $28.38 (confidence: 0.88)
  Method: keyword_total
  Candidates: 3

Invoice: INV-2024-001 (confidence: 0.75)
  Method: pattern_inv_dash
  Candidates: 1
```

## Creating Test Images

### Option 1: Use SROIE Dataset

Download the SROIE2019 dataset and use real receipt images:

```bash
# Download from: https://rrc.cvc.uab.es/?ch=13&com=downloads
# Extract to: tests/SROIE2019/

# Use dataset images
python examples/basic_usage.py tests/SROIE2019/train/img/X00016469612.jpg
```

### Option 2: Create Sample Receipt

Create a simple text receipt and convert to image:

```text
ACME Store
123 Main Street
City, State 12345

Invoice #: INV-2024-001
Date: 15/01/2024

Item 1: $10.00
Item 2: $15.80

Subtotal: $25.80
Tax: $2.58
Total: $28.38

Thank you for your business!
```

Save as image using:
- Screenshot tool
- Text-to-image converter
- Document editor (Word, Google Docs) → Export as PDF/Image

## Troubleshooting

### Import Errors

```bash
# Ensure you're in the project root
cd /path/to/adaptive-document-intelligence

# Run with Python module syntax
python -m examples.basic_usage
```

### Tesseract Not Found

```bash
# Verify installation
tesseract --version

# Set path if needed
export TESSERACT_CMD=/usr/local/bin/tesseract
```

### Low Accuracy

- Use clear, high-resolution images (300 DPI+)
- Ensure good lighting and contrast
- Avoid rotated or skewed images
- Try preprocessing: `processor = DocumentProcessor(use_preprocessing=True)`

## Next Steps

- Review [User Guide](../docs/user_guide.md) for detailed usage
- Check [API Reference](../docs/api_reference.md) for complete API
- See [Development Guide](../docs/development.md) for customization
- Run evaluation: `python scripts/run_evaluation.py --split train`

## Contributing Examples

To add a new example:

1. Create `examples/your_example.py`
2. Follow existing example structure
3. Add documentation to this README
4. Test with sample data
5. Submit pull request

---

**Need Help?**

- Check [FAQ](../docs/faq.md)
- Review [Troubleshooting](../docs/user_guide.md#troubleshooting)
- Create an issue with details