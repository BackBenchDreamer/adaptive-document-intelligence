# Troubleshooting Guide

Comprehensive troubleshooting guide for the Adaptive Document Intelligence System.

## Table of Contents

1. [OCR Subsystem Issues](#ocr-subsystem-issues)
   - [Common Error Messages](#common-error-messages)
   - [Platform-Specific Installation](#platform-specific-installation)
   - [Path Configuration](#path-configuration)
   - [Diagnostic Procedures](#diagnostic-procedures)
2. [Performance Issues](#performance-issues)
   - [Slow Processing Times](#slow-processing-times)
   - [Cache Configuration](#cache-configuration)
   - [Batch Processing Optimization](#batch-processing-optimization)
3. [Extraction Issues](#extraction-issues)
   - [Low Confidence Scores](#low-confidence-scores)
   - [Missing Field Extractions](#missing-field-extractions)
   - [Date Format Problems](#date-format-problems)
4. [System Validation](#system-validation)
   - [Running Validation Tests](#running-validation-tests)
   - [Interpreting Test Results](#interpreting-test-results)
   - [What to Do If Tests Fail](#what-to-do-if-tests-fail)
5. [Getting Help](#getting-help)
   - [Reporting Issues](#reporting-issues)
   - [Required Information](#required-information)
   - [Log Locations](#log-locations)

---

## OCR Subsystem Issues

The OCR subsystem is the foundation of the document processing pipeline. Most issues stem from incorrect installation or configuration of Tesseract OCR.

### Common Error Messages

#### Error: "pytesseract not installed"

**Cause:** The Python wrapper for Tesseract is not installed.

**Solution:**
```bash
# Install pytesseract package
pip install pytesseract>=0.3.10

# Verify installation
python -c "import pytesseract; print('pytesseract installed successfully')"
```

#### Error: "Tesseract not found" or "TesseractNotFoundError"

**Cause:** The Tesseract binary is not installed or not in the system PATH.

**Solution:**
1. Install Tesseract binary (see [Platform-Specific Installation](#platform-specific-installation))
2. Verify installation: `tesseract --version`
3. If installed but not detected, set `TESSERACT_CMD` environment variable

#### Error: "Failed to initialize OCR engine"

**Cause:** Multiple possible causes:
- Tesseract binary not found
- Incorrect path configuration
- Missing language data files

**Solution:**
```bash
# Run diagnostic script
python scripts/diagnose_ocr.py

# This will check:
# - Python package installation
# - Tesseract binary location
# - Language data availability
# - Path configuration
```

#### Error: "Unable to get tesseract version"

**Cause:** Tesseract is installed but the Python package cannot communicate with it.

**Solution:**
```bash
# Check Tesseract is accessible
tesseract --version

# If command not found, add to PATH or set TESSERACT_CMD
export TESSERACT_CMD=/path/to/tesseract

# Test Python integration
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

### Platform-Specific Installation

#### macOS

**Using Homebrew (Recommended):**
```bash
# Install Tesseract
brew install tesseract

# Verify installation
tesseract --version
which tesseract

# Common installation paths:
# Apple Silicon: /opt/homebrew/bin/tesseract
# Intel Mac: /usr/local/bin/tesseract
```

**Manual Installation:**
1. Download from: https://github.com/tesseract-ocr/tesseract/wiki
2. Follow installation instructions
3. Add to PATH or set `TESSERACT_CMD`

#### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt-get update

# Install Tesseract and English language data
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Verify installation
tesseract --version
which tesseract

# Common installation path: /usr/bin/tesseract
```

**Additional Languages:**
```bash
# Install additional language packs if needed
sudo apt-get install tesseract-ocr-fra  # French
sudo apt-get install tesseract-ocr-deu  # German
sudo apt-get install tesseract-ocr-spa  # Spanish
```

#### Linux (CentOS/RHEL/Fedora)

```bash
# Install Tesseract
sudo yum install tesseract

# Or on newer systems
sudo dnf install tesseract

# Verify installation
tesseract --version
```

#### Windows

1. **Download Installer:**
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest installer (e.g., `tesseract-ocr-w64-setup-v5.3.0.exe`)

2. **Install:**
   - Run the installer
   - Note the installation path (default: `C:\Program Files\Tesseract-OCR`)
   - Ensure "Add to PATH" is checked during installation

3. **Verify Installation:**
   ```cmd
   tesseract --version
   ```

4. **If Not in PATH:**
   ```cmd
   # Set environment variable (Command Prompt)
   set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

   # Or PowerShell
   $env:TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"

   # Or add to System PATH permanently via System Properties
   ```

### Path Configuration

The system automatically detects Tesseract in common installation paths:
- `/usr/bin/tesseract` (Linux)
- `/usr/local/bin/tesseract` (macOS Intel)
- `/opt/homebrew/bin/tesseract` (macOS Apple Silicon)
- `C:\Program Files\Tesseract-OCR\tesseract.exe` (Windows)

#### Manual Path Configuration

If automatic detection fails, set the path explicitly:

**Temporary (Current Session):**
```bash
# macOS/Linux
export TESSERACT_CMD=/path/to/tesseract

# Windows (Command Prompt)
set TESSERACT_CMD=C:\Path\To\tesseract.exe

# Windows (PowerShell)
$env:TESSERACT_CMD="C:\Path\To\tesseract.exe"
```

**Permanent Configuration:**

**macOS/Linux:**
Add to `~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`:
```bash
export TESSERACT_CMD=/opt/homebrew/bin/tesseract
```

**Windows:**
1. Open System Properties → Advanced → Environment Variables
2. Add new User or System variable:
   - Name: `TESSERACT_CMD`
   - Value: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**In Python Code:**
```python
import os
os.environ['TESSERACT_CMD'] = '/path/to/tesseract'

from pipeline.pipeline import DocumentProcessor
processor = DocumentProcessor(ocr_engine='tesseract')
```

### Diagnostic Procedures

#### Step 1: Run Built-in Diagnostic

```bash
python scripts/diagnose_ocr.py
```

This script checks:
- Python package installation
- Tesseract binary availability
- Path configuration
- Version compatibility
- Language data files

#### Step 2: Manual Verification

```bash
# Check Tesseract binary
tesseract --version

# Check Python package
python -c "import pytesseract; print(pytesseract.__version__)"

# Test OCR functionality
python -c "
import pytesseract
from PIL import Image
print(pytesseract.get_tesseract_version())
"
```

#### Step 3: Test with Sample Image

```bash
# Create a test image with text
echo "Test OCR" | convert -pointsize 48 label:@- test.png

# Run OCR
tesseract test.png stdout

# Test through Python
python -c "
import pytesseract
from PIL import Image
img = Image.open('test.png')
text = pytesseract.image_to_string(img)
print(f'Extracted: {text}')
"
```

#### Step 4: Check System Validation

```bash
# Run full system validation
python validate_system.py

# Expected output:
# ✓ All imports successful
# ✓ Tesseract OCR detected
# ✓ System ready for processing
```

---

## Performance Issues

### Slow Processing Times

**Symptoms:**
- Processing takes longer than expected
- Batch processing is very slow
- System appears to hang

**Common Causes and Solutions:**

#### 1. Large Image Files

**Problem:** High-resolution images take longer to process.

**Solution:**
```python
from pipeline.pipeline import DocumentProcessor

# Resize images before processing
processor = DocumentProcessor(
    ocr_engine='tesseract',
    max_image_size=(1920, 1080)  # Resize to max dimensions
)
```

#### 2. Inefficient Batch Processing

**Problem:** Processing images one at a time without optimization.

**Solution:**
```bash
# Use batch processing with parallel execution
python scripts/run_pipeline.py --batch images/ --workers 4
```

Or in code:
```python
from concurrent.futures import ThreadPoolExecutor
from pipeline.pipeline import DocumentProcessor

processor = DocumentProcessor()

def process_image(image_path):
    return processor.process_document(image_path)

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_image, image_paths))
```

#### 3. OCR Engine Performance

**Problem:** Tesseract can be slow on certain images.

**Solution:**
```python
# Try PaddleOCR for faster processing (requires installation)
pip install paddlepaddle paddleocr

processor = DocumentProcessor(ocr_engine='paddleocr')
```

#### 4. Disk I/O Bottleneck

**Problem:** Reading/writing many files slows down processing.

**Solution:**
- Use SSD storage for data directories
- Process images in memory when possible
- Batch write results instead of writing after each image

### Cache Configuration

The system uses caching to improve performance on repeated operations.

**Enable Caching:**
```python
from pipeline.pipeline import DocumentProcessor

processor = DocumentProcessor(
    cache_enabled=True,
    cache_dir='./cache'
)
```

**Clear Cache:**
```bash
# Remove cache directory
rm -rf ./cache

# Or in Python
import shutil
shutil.rmtree('./cache', ignore_errors=True)
```

**Cache Statistics:**
```python
# Check cache hit rate
processor.get_cache_stats()
```

### Batch Processing Optimization

**Best Practices:**

1. **Use Appropriate Batch Sizes:**
```bash
# Process in chunks of 100
python scripts/run_pipeline.py --batch images/ --chunk-size 100
```

2. **Monitor Memory Usage:**
```python
import psutil

# Check memory before processing
memory = psutil.virtual_memory()
print(f"Available memory: {memory.available / 1024**3:.2f} GB")
```

3. **Use Progress Tracking:**
```bash
# Enable progress bar
python scripts/run_pipeline.py --batch images/ --progress
```

4. **Optimize Output:**
```bash
# Write results in batches
python scripts/run_pipeline.py --batch images/ --output-batch-size 50
```

---

## Extraction Issues

### Low Confidence Scores

**Symptoms:**
- Confidence scores consistently below 0.7
- Many fields marked as low confidence
- Extraction results seem correct but confidence is low

**Causes and Solutions:**

#### 1. Poor Image Quality

**Problem:** Blurry, low-contrast, or noisy images.

**Solution:**
```python
from PIL import Image, ImageEnhance

# Preprocess image
img = Image.open('receipt.jpg')

# Increase contrast
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(1.5)

# Increase sharpness
enhancer = ImageEnhance.Sharpness(img)
img = enhancer.enhance(2.0)

# Process enhanced image
result = processor.process_document(img)
```

#### 2. OCR Errors

**Problem:** OCR misreads characters, affecting confidence.

**Solution:**
```bash
# Check OCR quality
python scripts/run_pipeline.py --image receipt.jpg --show-ocr-text

# Try different OCR engine
python scripts/run_pipeline.py --image receipt.jpg --ocr-engine paddleocr
```

#### 3. Extraction Pattern Mismatch

**Problem:** Document format doesn't match expected patterns.

**Solution:**
```python
from pipeline.extractor import FieldExtractor

# Customize extraction patterns
extractor = FieldExtractor()

# Add custom date pattern
extractor.add_date_pattern(r'\d{4}/\d{2}/\d{2}')

# Add custom total pattern
extractor.add_total_pattern(r'Total:\s*\$?(\d+\.\d{2})')
```

#### 4. Confidence Calibration

**Problem:** Confidence scores not calibrated to actual accuracy.

**Solution:**
```bash
# Analyze confidence calibration
python scripts/analyze_confidence.py --calibrate

# Use calibrated scores
processor = DocumentProcessor(use_calibrated_confidence=True)
```

### Missing Field Extractions

**Symptoms:**
- Some fields not extracted
- Fields extracted as `null` or empty
- Inconsistent extraction across similar documents

**Debugging Steps:**

#### 1. Check OCR Output

```bash
# View raw OCR text
python scripts/run_pipeline.py --image receipt.jpg --debug-ocr
```

#### 2. Verify Field Patterns

```python
from pipeline.extractor import FieldExtractor

extractor = FieldExtractor()

# Test pattern matching
text = "Total: $123.45"
result = extractor.extract_total(text)
print(f"Extracted: {result}")
```

#### 3. Check Field Locations

```python
# Enable location-based extraction
processor = DocumentProcessor(use_location_hints=True)

# Specify expected field locations
result = processor.process_document(
    'receipt.jpg',
    field_hints={
        'total': {'region': 'bottom'},
        'date': {'region': 'top'},
        'invoice_number': {'region': 'top-right'}
    }
)
```

#### 4. Analyze Extraction Errors

```bash
# Run error analysis
python scripts/run_error_analysis.py --image receipt.jpg --show-details
```

### Date Format Problems

**Symptoms:**
- Dates not recognized
- Dates extracted in wrong format
- Date parsing errors

**Common Date Formats:**

The system supports multiple date formats:
- `DD/MM/YYYY` (e.g., 25/12/2023)
- `MM/DD/YYYY` (e.g., 12/25/2023)
- `YYYY-MM-DD` (e.g., 2023-12-25)
- `DD-MM-YYYY` (e.g., 25-12-2023)
- `DD.MM.YYYY` (e.g., 25.12.2023)
- `Month DD, YYYY` (e.g., December 25, 2023)

**Solutions:**

#### 1. Add Custom Date Format

```python
from pipeline.extractor import FieldExtractor

extractor = FieldExtractor()

# Add custom date pattern
extractor.add_date_pattern(
    pattern=r'\d{4}/\d{2}/\d{2}',
    format='%Y/%m/%d'
)
```

#### 2. Specify Date Format Preference

```python
processor = DocumentProcessor(
    preferred_date_format='DD/MM/YYYY'
)
```

#### 3. Handle Ambiguous Dates

```python
# Configure date parsing
processor = DocumentProcessor(
    date_parsing_mode='strict',  # or 'lenient'
    assume_day_first=True  # For DD/MM/YYYY vs MM/DD/YYYY
)
```

---

## System Validation

### Running Validation Tests

#### Full System Validation

```bash
# Run complete validation
python validate_system.py

# Expected output:
# ✓ All imports successful
# ✓ Tesseract OCR detected
# ✓ System ready for processing
```

#### Component-Specific Tests

```bash
# Test OCR only
pytest tests/unit/test_ocr.py -v

# Test extraction only
pytest tests/unit/test_extractor.py -v

# Test confidence scoring
pytest tests/unit/test_confidence.py -v

# Test full pipeline
pytest tests/integration/test_pipeline.py -v
```

#### End-to-End Tests

```bash
# Run E2E tests
pytest tests/e2e/ -v

# Test with sample images
pytest tests/e2e/test_full_pipeline.py -v
```

### Interpreting Test Results

#### Successful Test Output

```
tests/unit/test_ocr.py::test_tesseract_initialization PASSED
tests/unit/test_ocr.py::test_text_extraction PASSED
tests/unit/test_extractor.py::test_date_extraction PASSED
tests/unit/test_extractor.py::test_total_extraction PASSED

======================== 4 passed in 2.34s ========================
```

#### Failed Test Output

```
tests/unit/test_ocr.py::test_tesseract_initialization FAILED

FAILED tests/unit/test_ocr.py::test_tesseract_initialization
E   TesseractNotFoundError: Tesseract is not installed
```

**Action:** Follow OCR troubleshooting steps above.

#### Skipped Tests

```
tests/integration/test_sroie.py::test_sroie_evaluation SKIPPED
Reason: SROIE dataset not available
```

**Action:** This is normal if you haven't downloaded the SROIE dataset.

### What to Do If Tests Fail

#### Step 1: Identify the Failure

```bash
# Run tests with verbose output
pytest -v --tb=short

# Run specific failing test
pytest tests/unit/test_ocr.py::test_tesseract_initialization -v
```

#### Step 2: Check Dependencies

```bash
# Verify all dependencies installed
pip install -r requirements.txt

# Check for missing packages
pip check
```

#### Step 3: Check Configuration

```bash
# Verify environment variables
echo $TESSERACT_CMD
echo $OCR_ENGINE

# Check Python version
python --version  # Should be 3.11+
```

#### Step 4: Run Diagnostics

```bash
# Run OCR diagnostic
python scripts/diagnose_ocr.py

# Run system validation
python validate_system.py
```

#### Step 5: Check Logs

```bash
# View recent logs
tail -n 100 logs/system.log

# Search for errors
grep -i error logs/system.log
```

---

## Getting Help

### Reporting Issues

When reporting issues, please include:

1. **System Information:**
   ```bash
   # Collect system info
   python -c "
   import sys
   import platform
   print(f'Python: {sys.version}')
   print(f'Platform: {platform.platform()}')
   print(f'Architecture: {platform.machine()}')
   "
   ```

2. **Tesseract Information:**
   ```bash
   tesseract --version
   which tesseract  # or 'where tesseract' on Windows
   ```

3. **Package Versions:**
   ```bash
   pip list | grep -E "(pytesseract|pillow|opencv)"
   ```

4. **Error Messages:**
   - Full error traceback
   - Relevant log entries
   - Steps to reproduce

### Required Information

When seeking help, provide:

- **Environment Details:**
  - Operating system and version
  - Python version
  - Tesseract version
  - Installation method (pip, conda, system package manager)

- **Error Context:**
  - What you were trying to do
  - What happened instead
  - Error messages (full traceback)
  - Relevant code snippets

- **Diagnostic Output:**
  ```bash
  # Run and include output
  python scripts/diagnose_ocr.py
  python validate_system.py
  ```

- **Sample Data (if applicable):**
  - Sample image (if not confidential)
  - Expected vs actual output
  - Configuration used

### Log Locations

**Default Log Locations:**

- **System Logs:** `logs/system.log`
- **Error Logs:** `logs/errors.log`
- **Processing Logs:** `logs/processing.log`

**View Logs:**

```bash
# View all logs
tail -f logs/system.log

# View errors only
tail -f logs/errors.log

# Search logs
grep -i "error" logs/system.log
grep -i "tesseract" logs/system.log
```

**Log Levels:**

Configure logging verbosity:

```python
import logging
from core.logging_config import setup_logging

# Set log level
setup_logging(level=logging.DEBUG)  # DEBUG, INFO, WARNING, ERROR
```

Or via environment variable:

```bash
export LOG_LEVEL=DEBUG
python scripts/run_pipeline.py --image receipt.jpg
```

**Log Rotation:**

Logs are automatically rotated:
- Max size: 10 MB per file
- Backup count: 5 files
- Old logs are compressed

**Clear Logs:**

```bash
# Remove all logs
rm -rf logs/*.log

# Remove old logs only
find logs/ -name "*.log.*" -delete
```

---

## Additional Resources

- **[README.md](../README.md)** - Quick start and basic usage
- **[Architecture Documentation](ARCHITECTURE.md)** - System design details
- **[API Reference](api_reference.md)** - Detailed API documentation
- **[User Guide](user_guide.md)** - Comprehensive usage guide
- **[Development Guide](development.md)** - Contributing guidelines
- **[FAQ](faq.md)** - Frequently asked questions

---

## Quick Reference

### Common Commands

```bash
# Diagnose OCR issues
python scripts/diagnose_ocr.py

# Validate system
python validate_system.py

# Process single image
python scripts/run_pipeline.py --image receipt.jpg

# Run tests
pytest tests/

# View logs
tail -f logs/system.log
```

### Environment Variables

```bash
# Tesseract path
export TESSERACT_CMD=/path/to/tesseract

# OCR engine selection
export OCR_ENGINE=tesseract  # or 'paddleocr'

# Log level
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR

# Data directories
export DATA_DIR=./data
export OUTPUT_DIR=./output
```

### Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| pytesseract not installed | `pip install pytesseract>=0.3.10` |
| Tesseract not found | Install Tesseract binary for your OS |
| Import errors | `pip install -r requirements.txt` |
| Low confidence | Check image quality, try preprocessing |
| Missing fields | Verify OCR output, check extraction patterns |
| Slow processing | Use batch processing, enable caching |

---

**Last Updated:** 2026-04-27  
**Version:** 1.0.0  
**Status:** Production-ready