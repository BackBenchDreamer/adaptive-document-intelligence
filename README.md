# Adaptive Document Intelligence System

Production-grade document processing pipeline for extracting structured data from receipts and invoices using OCR and intelligent field extraction.

## Overview

This system provides an end-to-end pipeline for processing document images:
- **OCR**: Extract text using Tesseract (required) or PaddleOCR (optional)
- **Extraction**: Intelligent field extraction for dates, totals, and invoice numbers
- **Confidence Scoring**: Multi-factor confidence assessment
- **Evaluation**: Comprehensive metrics and error analysis

## System Architecture

```
Image → OCR (Tesseract) → Field Extraction → Confidence Scoring → JSON Output
```

### Key Features

- ✅ **Tesseract OCR** - Primary OCR engine (REQUIRED)
- ✅ **PaddleOCR Support** - Optional fallback OCR engine
- ✅ **Smart Field Extraction** - Pattern-based extraction with scoring
- ✅ **Confidence Assessment** - Multi-factor confidence scoring
- ✅ **Batch Processing** - Process multiple documents efficiently
- ✅ **SROIE2019 Dataset** - Built-in support for evaluation
- ✅ **Docker Support** - Containerized deployment
- ✅ **Comprehensive Testing** - Unit, integration, and E2E tests

## Quick Start

### Prerequisites

**System Requirements:**
- Python 3.11+
- Tesseract OCR (REQUIRED)

**Install Tesseract:**

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

**Note:** The system automatically detects Tesseract in common installation paths. If Tesseract is installed but not detected, set the `TESSERACT_CMD` environment variable:

```bash
export TESSERACT_CMD=/path/to/tesseract
```

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd adaptive-document-intelligence

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation
python -c "from pipeline.pipeline import DocumentProcessor; print('✓ Installation successful')"
```

### Basic Usage

```python
from pipeline.pipeline import DocumentProcessor

# Initialize processor with Tesseract
processor = DocumentProcessor(ocr_engine='tesseract')

# Process a single document
result = processor.process_document('receipt.jpg')

# Access extracted fields
print(f"Date: {result['fields']['date']['value']}")
print(f"Total: ${result['fields']['total']['value']:.2f}")
print(f"Invoice: {result['fields']['invoice_number']['value']}")
```

### Command Line Usage

```bash
# Process single image
python scripts/run_pipeline.py --image receipt.jpg

# Batch processing
python scripts/run_pipeline.py --batch images/ --output results.json

# Process SROIE dataset
python scripts/run_pipeline.py --sroie train --limit 100
```
### Advanced Usage

#### Evaluation
Evaluate system performance on SROIE dataset:
```bash
# Basic evaluation
python scripts/run_evaluation.py --split train --limit 100

# With calibration analysis and detailed output
python scripts/run_evaluation.py --split train --show-calibration --verbose --output results.json
```

#### Error Analysis
Analyze extraction errors and patterns:
```bash
# Show error examples
python scripts/run_error_analysis.py --split train --show-examples

# Generate HTML report
python scripts/run_error_analysis.py --split train --generate-report --output report.json
```

#### Confidence Analysis
Analyze confidence score distribution and calibration:
```bash
# Analyze confidence scores
python scripts/analyze_confidence.py --samples 100

# Generate calibration data
python scripts/analyze_confidence.py --calibrate --output calibration.json

# Compare calibrated vs uncalibrated
python scripts/analyze_confidence.py --compare
```

#### Docker Helper
Run any script in Docker container:
```bash
# Process documents
./scripts/docker_run.sh pipeline --image receipt.jpg

# Run evaluation
./scripts/docker_run.sh evaluation --split train

# Run error analysis
./scripts/docker_run.sh error-analysis --split train

# Open interactive shell
./scripts/docker_run.sh shell

# Run tests
./scripts/docker_run.sh test
```


## Configuration

### OCR Engine Selection

**Tesseract (Default, REQUIRED):**
```python
processor = DocumentProcessor(ocr_engine='tesseract')
```

**PaddleOCR (Optional):**
```python
# First install: pip install paddlepaddle paddleocr
processor = DocumentProcessor(ocr_engine='paddleocr')
```

### Environment Variables

```bash
# Specify Tesseract location (if not in PATH)
export TESSERACT_CMD=/usr/local/bin/tesseract

# Choose OCR engine
export OCR_ENGINE=tesseract  # or 'paddleocr'

# Data directories
export DATA_DIR=./data
export OUTPUT_DIR=./output
```

## Dataset Setup (Optional)

For evaluation and testing with SROIE2019 dataset:

1. Download SROIE2019 from: https://rrc.cvc.uab.es/?ch=13&com=downloads
2. Extract to `tests/SROIE2019/`
3. Structure should be:
   ```
   tests/SROIE2019/
   ├── train/
   │   ├── img/
   │   └── box/
   └── test/
       ├── img/
       └── box/
   ```

**Note:** Dataset is excluded from git via `.gitignore`

## Docker Deployment

```bash
# Build image
docker build -t adi-system .

# Run tests
docker run adi-system

# Process images (mount volume)
docker run -v $(pwd)/images:/app/images adi-system \
  python scripts/run_pipeline.py --batch /app/images
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## Project Structure

```
adaptive-document-intelligence/
├── core/                   # Core infrastructure
│   ├── config.py          # Configuration management
│   ├── logging_config.py  # Logging setup
│   └── utils.py           # Utility functions
├── pipeline/              # Processing pipeline
│   ├── ocr.py            # OCR engines (Tesseract/PaddleOCR)
│   ├── extractor.py      # Field extraction
│   ├── confidence.py     # Confidence scoring
│   └── pipeline.py       # End-to-end pipeline
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/              # End-to-end tests
│   ├── data/             # Data loaders
│   ├── metrics/          # Evaluation metrics
│   └── analysis/         # Error analysis
├── scripts/               # CLI scripts
├── examples/              # Usage examples
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
└── README.md             # This file
```

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[API Reference](docs/api_reference.md)** - Detailed API documentation
- **[User Guide](docs/user_guide.md)** - Comprehensive usage guide
- **[Development](docs/development.md)** - Development guidelines
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Comprehensive troubleshooting guide
- **[FAQ](docs/faq.md)** - Frequently asked questions

## Performance

Typical processing times (on standard hardware):
- Single image: 0.5-2 seconds
- Batch (100 images): 1-3 minutes
- OCR: 60-70% of processing time
- Extraction + Confidence: 30-40% of processing time

## Troubleshooting

### Quick Fix

If you see "pytesseract not installed" or "Tesseract not found":

```bash
# Install pytesseract Python package
pip install pytesseract>=0.3.10

# Verify installation
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

If Tesseract binary is not installed, see detailed instructions below.

### Verification

After fixing, verify the system works:

```bash
# Run system validation
python validate_system.py

# Test with a single image
python scripts/run_pipeline.py --image path/to/image.jpg

# Run diagnostic script
python scripts/diagnose_ocr.py
```

Expected output for successful validation:
- ✓ All imports successful
- ✓ Tesseract OCR detected
- ✓ System ready for processing

### Tesseract OCR Troubleshooting

#### Issue: "pytesseract not installed" or "Tesseract not found"

If you encounter OCR initialization errors, follow these steps:

##### 1. Install pytesseract Python package
```bash
pip install pytesseract>=0.3.10
```

##### 2. Install Tesseract binary

**macOS (Homebrew):**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

##### 3. Verify Installation

Check that Tesseract is installed:
```bash
tesseract --version
```

Test Python integration:
```bash
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

##### 4. Manual Path Configuration (if needed)

If Tesseract is installed but not detected, set the path explicitly:

**macOS/Linux:**
```bash
export TESSERACT_CMD=/opt/homebrew/bin/tesseract  # macOS Homebrew
# or
export TESSERACT_CMD=/usr/local/bin/tesseract     # macOS Intel
# or
export TESSERACT_CMD=/usr/bin/tesseract           # Linux
```

**Windows:**
```cmd
set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

##### 5. Run Diagnostic Script

Use the built-in diagnostic tool:
```bash
python scripts/diagnose_ocr.py
```

This will check your environment and provide specific guidance.

### Import Errors

```bash
# Ensure all dependencies installed
pip install -r requirements.txt

# Verify Python version
python --version  # Should be 3.11+
```

### Low Accuracy

- Ensure images are clear and well-lit
- Check OCR confidence scores
- Verify field extraction patterns match your document format
- Consider preprocessing images (contrast, rotation)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Acknowledgments

- SROIE2019 dataset: https://rrc.cvc.uab.es/?ch=13
- Tesseract OCR: https://github.com/tesseract-ocr/tesseract
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR

---

**Status:** Production-ready v1.0.0  
**Python:** 3.11+  
**Primary OCR:** Tesseract (REQUIRED)  
**Optional OCR:** PaddleOCR
