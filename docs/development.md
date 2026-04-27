# Development Guide

Complete guide for developers contributing to the Adaptive Document Intelligence System.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Structure](#code-structure)
3. [Coding Standards](#coding-standards)
4. [Adding New Features](#adding-new-features)
5. [Testing Guidelines](#testing-guidelines)
6. [Debugging Tips](#debugging-tips)
7. [Performance Profiling](#performance-profiling)
8. [Contributing](#contributing)

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv or conda)
- Code editor (VS Code recommended)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd adaptive-document-intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### IDE Setup (VS Code)

Recommended extensions:
- Python (Microsoft)
- Pylance
- Python Test Explorer
- GitLens

**`.vscode/settings.json`:**
```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "editor.formatOnSave": true,
    "editor.rulers": [88]
}
```

### Environment Configuration

Create `.env` file:
```bash
# OCR Configuration
OCR_ENGINE=tesseract
TESSERACT_CMD=/opt/homebrew/bin/tesseract

# Development Settings
LOG_LEVEL=DEBUG
ENABLE_CACHE=true

# Dataset Path
DATASET_PATH=tests/SROIE2019
```

---

## Code Structure

### Directory Organization

```
adaptive-document-intelligence/
├── core/                   # Core infrastructure
│   ├── config.py          # Configuration management
│   ├── logging_config.py  # Logging setup
│   └── utils.py           # Utility functions
│
├── pipeline/              # Processing pipeline
│   ├── ocr.py            # OCR engines
│   ├── extractor.py      # Field extraction
│   ├── confidence.py     # Confidence scoring
│   └── pipeline.py       # Pipeline orchestration
│
├── tests/                 # Test suite
│   ├── data/             # Dataset loader
│   ├── metrics/          # Evaluation metrics
│   ├── analysis/         # Error analysis
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
│
├── scripts/               # CLI tools
│   ├── run_pipeline.py   # Main processing script
│   ├── run_evaluation.py # Evaluation script
│   └── run_error_analysis.py  # Error analysis
│
├── docs/                  # Documentation
└── output/                # Generated files
```

### Module Dependencies

```
core/
  └─> (no dependencies)

pipeline/ocr.py
  └─> core/

pipeline/extractor.py
  └─> core/

pipeline/confidence.py
  └─> core/

pipeline/pipeline.py
  └─> core/, pipeline/ocr, pipeline/extractor, pipeline/confidence

tests/data/
  └─> core/

tests/metrics/
  └─> core/, tests/data/

scripts/
  └─> core/, pipeline/, tests/
```

---

## Coding Standards

### Python Style Guide

Follow PEP 8 with these specifics:

**Line Length:**
- Maximum 88 characters (Black default)
- Use line breaks for readability

**Naming Conventions:**
```python
# Classes: PascalCase
class DocumentProcessor:
    pass

# Functions/methods: snake_case
def process_document(image_path):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_BATCH_SIZE = 1000

# Private methods: _leading_underscore
def _internal_helper(self):
    pass
```

**Imports:**
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import numpy as np
from PIL import Image

# Local
from core.config import Config
from pipeline.ocr import OCRManager
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import Dict, List, Optional, Tuple

def extract_text(
    image_path: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Extract text from image.
    
    Args:
        image_path: Path to image file
        use_cache: Whether to use cached results
        
    Returns:
        Dictionary with extracted text and metadata
    """
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_confidence(
    extraction_result: Dict,
    ocr_result: Dict,
    field_name: str
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate multi-factor confidence score.
    
    Combines extraction confidence, OCR quality, validity, and
    pattern strength into a single calibrated score.
    
    Args:
        extraction_result: Output from field extractor with keys:
            - value: Extracted value
            - confidence: Base confidence score
            - raw_value: Original text
        ocr_result: Output from OCR module with keys:
            - text: Extracted text
            - confidence: OCR confidence
        field_name: Field type ('date', 'total', 'invoice_number')
        
    Returns:
        Tuple of (final_confidence, factor_breakdown) where:
        - final_confidence: Calibrated score in [0, 1]
        - factor_breakdown: Dict with individual factor scores
        
    Example:
        >>> confidence, factors = calculate_confidence(
        ...     {'value': '2024-01-15', 'confidence': 0.9},
        ...     {'text': 'Receipt text...', 'confidence': 0.85},
        ...     'date'
        ... )
        >>> print(f"Confidence: {confidence:.2f}")
        Confidence: 0.87
    """
    pass
```

### Error Handling

```python
# Specific exceptions
try:
    result = process_document(image_path)
except FileNotFoundError:
    logger.error(f"Image not found: {image_path}")
    raise
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    return create_error_result(str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise

# Context managers for resources
with open(file_path, 'r') as f:
    data = json.load(f)
```

### Logging

```python
from core.logging_config import get_logger

logger = get_logger(__name__)

# Log levels
logger.debug("Detailed information for debugging")
logger.info("General information about progress")
logger.warning("Warning about potential issues")
logger.error("Error that needs attention")

# Structured logging with context
logger.info(
    "Processing document",
    extra={
        'image_id': 'X123',
        'processing_time': 1.23,
        'confidence': 0.85
    }
)
```

---

## Adding New Features

### Adding a New OCR Engine

1. **Create engine class:**

```python
# pipeline/ocr.py

class CustomOCREngine(OCREngine):
    """Custom OCR engine implementation."""
    
    def __init__(self, **kwargs):
        """Initialize engine with configuration."""
        self.config = kwargs
        self._available = None
    
    def is_available(self) -> bool:
        """Check if engine is available."""
        try:
            # Check if engine can be initialized
            return True
        except Exception:
            return False
    
    def extract_text(self, image_path: str) -> Dict:
        """Extract text using custom engine."""
        start_time = time.time()
        
        try:
            # Implement extraction logic
            text = self._perform_ocr(image_path)
            confidence = self._calculate_confidence()
            
            return {
                'text': text,
                'confidence': confidence,
                'engine': 'custom',
                'processing_time': time.time() - start_time,
                'metadata': {}
            }
        except Exception as e:
            logger.error(f"Custom OCR failed: {e}")
            return self._create_error_result(image_path, e)
```

2. **Register in OCRManager:**

```python
# pipeline/ocr.py - OCRManager.__init__

self.engines = {
    'paddleocr': PaddleOCREngine(...),
    'tesseract': TesseractEngine(...),
    'custom': CustomOCREngine(...)  # Add here
}
```

3. **Add tests:**

```python
# tests/unit/test_ocr.py

class TestCustomOCREngine(unittest.TestCase):
    def test_is_available(self):
        engine = CustomOCREngine()
        self.assertIsInstance(engine.is_available(), bool)
    
    def test_extract_text(self):
        engine = CustomOCREngine()
        result = engine.extract_text('test_image.jpg')
        self.assertIn('text', result)
        self.assertIn('confidence', result)
```

### Adding a New Field Extractor

1. **Create extractor class:**

```python
# pipeline/extractor.py

class CompanyExtractor(FieldExtractor):
    """Extract company name from OCR text."""
    
    def __init__(self):
        """Initialize patterns and keywords."""
        self.patterns = [
            r'\b([A-Z][a-z]+ (?:Inc|LLC|Ltd|Corp)\.?)\b',
            r'\b([A-Z][A-Z\s]+)\b'  # All caps company names
        ]
        
        self.keywords = ['company', 'merchant', 'store']
    
    def extract(self, text: str) -> Dict:
        """Extract company name from text."""
        start_time = time.time()
        
        # Find candidates
        candidates = self._find_candidates(text)
        
        if not candidates:
            return {
                'value': None,
                'confidence': 0.0,
                'candidates': [],
                'method': 'no_candidates',
                'metadata': {'extraction_time': time.time() - start_time}
            }
        
        # Score and select best
        scored = self._score_candidates(candidates, text)
        best = max(scored, key=lambda x: x['score'])
        
        return {
            'value': best['value'],
            'confidence': best['score'],
            'raw_value': best['raw_value'],
            'candidates': scored,
            'method': 'pattern_match',
            'metadata': {'extraction_time': time.time() - start_time}
        }
```

2. **Add to ExtractionManager:**

```python
# pipeline/extractor.py - ExtractionManager

class ExtractionManager:
    def __init__(self):
        self.date_extractor = DateExtractor()
        self.total_extractor = TotalExtractor()
        self.invoice_extractor = InvoiceNumberExtractor()
        self.company_extractor = CompanyExtractor()  # Add here
    
    def extract_fields(self, ocr_result: Dict) -> Dict:
        # Extract all fields including company
        company_result = self.company_extractor.extract(text)
        
        return {
            'date': date_result,
            'total': total_result,
            'invoice_number': invoice_result,
            'company': company_result  # Add to result
        }
```

3. **Add tests:**

```python
# tests/unit/test_extractor.py

class TestCompanyExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = CompanyExtractor()
    
    def test_extract_company(self):
        text = "ACME Corp\nReceipt #123"
        result = self.extractor.extract(text)
        self.assertEqual(result['value'], 'ACME Corp')
        self.assertGreater(result['confidence'], 0.5)
```

### Adding a New Confidence Factor

1. **Update MultiFactorConfidenceScorer:**

```python
# pipeline/confidence.py

class MultiFactorConfidenceScorer(ConfidenceScorer):
    def __init__(self):
        self.weights = {
            'extraction': 0.35,      # Reduced
            'ocr_quality': 0.25,     # Reduced
            'validity': 0.20,
            'pattern': 0.10,
            'context': 0.10          # New factor
        }
    
    def calculate_confidence(self, ...):
        # Calculate existing factors
        extraction_conf = ...
        ocr_quality = ...
        validity_score = ...
        pattern_strength = ...
        
        # Calculate new factor
        context_score = self._calculate_context_score(
            extraction_result,
            ocr_result
        )
        
        # Combine with weights
        final_confidence = (
            extraction_conf * self.weights['extraction'] +
            ocr_quality * self.weights['ocr_quality'] +
            validity_score * self.weights['validity'] +
            pattern_strength * self.weights['pattern'] +
            context_score * self.weights['context']
        )
        
        return final_confidence, {
            'extraction': extraction_conf,
            'ocr_quality': ocr_quality,
            'validity': validity_score,
            'pattern': pattern_strength,
            'context': context_score
        }
    
    def _calculate_context_score(self, extraction_result, ocr_result):
        """Calculate context-based confidence."""
        # Implementation
        return 0.8
```

---

## Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Test individual functions/classes
├── integration/       # Test module interactions
├── e2e/              # Test complete workflows
├── fixtures/         # Test data
└── conftest.py       # Pytest configuration
```

### Writing Unit Tests

```python
# tests/unit/test_extractor.py

import unittest
from pipeline.extractor import DateExtractor

class TestDateExtractor(unittest.TestCase):
    """Test DateExtractor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = DateExtractor()
    
    def test_extract_date_ddmmyyyy(self):
        """Test DD/MM/YYYY format extraction."""
        text = "Date: 15/01/2024"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], '2024-01-15')
        self.assertGreater(result['confidence'], 0.7)
    
    def test_extract_date_no_match(self):
        """Test extraction with no date present."""
        text = "No date here"
        result = self.extractor.extract(text)
        
        self.assertIsNone(result['value'])
        self.assertEqual(result['confidence'], 0.0)
    
    def test_extract_date_multiple_candidates(self):
        """Test extraction with multiple date candidates."""
        text = "Invoice Date: 15/01/2024\nDue Date: 30/01/2024"
        result = self.extractor.extract(text)
        
        # Should prefer first date near "Invoice Date"
        self.assertEqual(result['value'], '2024-01-15')
        self.assertGreater(len(result['candidates']), 1)
```

### Writing Integration Tests

```python
# tests/integration/test_pipeline_integration.py

import unittest
from pipeline import DocumentProcessor

class TestPipelineIntegration(unittest.TestCase):
    """Test integration between pipeline components."""
    
    def setUp(self):
        self.processor = DocumentProcessor(ocr_engine='tesseract')
    
    def test_ocr_to_extraction(self):
        """Test OCR output flows correctly to extraction."""
        # Mock OCR result
        ocr_result = {
            'text': 'Date: 15/01/2024\nTotal: $25.80',
            'confidence': 0.9
        }
        
        # Extract fields
        from pipeline.extractor import ExtractionManager
        extractor = ExtractionManager()
        result = extractor.extract_fields(ocr_result)
        
        self.assertIn('date', result)
        self.assertIn('total', result)
        self.assertEqual(result['date']['value'], '2024-01-15')
        self.assertEqual(result['total']['value'], 25.80)
```

### Writing E2E Tests

```python
# tests/e2e/test_full_pipeline.py

import unittest
from pathlib import Path
from pipeline import DocumentProcessor

class TestFullPipeline(unittest.TestCase):
    """Test complete document processing pipeline."""
    
    def setUp(self):
        self.processor = DocumentProcessor()
        self.test_image = 'tests/fixtures/sample_receipt.jpg'
    
    def test_process_document_end_to_end(self):
        """Test processing a document from image to result."""
        result = self.processor.process_document(self.test_image)
        
        # Verify structure
        self.assertIn('fields', result)
        self.assertIn('metadata', result)
        self.assertTrue(result['metadata']['success'])
        
        # Verify fields
        self.assertIsNotNone(result['fields']['date']['value'])
        self.assertIsNotNone(result['fields']['total']['value'])
        
        # Verify confidence scores
        self.assertGreater(result['fields']['date']['confidence'], 0.0)
        self.assertLessEqual(result['fields']['date']['confidence'], 1.0)
```

### Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test file
pytest tests/unit/test_extractor.py -v

# Run specific test class
pytest tests/unit/test_extractor.py::TestDateExtractor -v

# Run specific test method
pytest tests/unit/test_extractor.py::TestDateExtractor::test_extract_date_ddmmyyyy -v

# Run with coverage
pytest --cov=pipeline --cov-report=html

# Run with markers
pytest -m "not slow"  # Skip slow tests
```

### Test Coverage

Aim for:
- **Unit tests**: >90% coverage
- **Integration tests**: All module interactions
- **E2E tests**: All major workflows

Check coverage:
```bash
pytest --cov=pipeline --cov=core --cov-report=term-missing
```

---

## Debugging Tips

### Logging for Debugging

```python
# Enable debug logging
from core.config import Config
Config.LOG_LEVEL = 'DEBUG'

# Or via environment
export LOG_LEVEL=DEBUG
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in (Python 3.7+)
breakpoint()

# VS Code debugger
# Set breakpoints in IDE and run with debugger
```

### Common Issues

**Issue: OCR returns empty text**
```python
# Debug OCR
from pipeline.ocr import OCRManager

manager = OCRManager()
result = manager.extract_text('image.jpg')
print(f"Text length: {len(result['text'])}")
print(f"Confidence: {result['confidence']}")
print(f"Engine: {result['engine']}")

# Check preprocessing
result_preprocessed = manager.extract_text('image.jpg', preprocess=True)
```

**Issue: Low extraction confidence**
```python
# Debug extraction
from pipeline.extractor import DateExtractor

extractor = DateExtractor()
result = extractor.extract(text)

# Check candidates
print(f"Candidates found: {len(result['candidates'])}")
for candidate in result['candidates']:
    print(f"  {candidate['raw_value']}: {candidate['score']:.2f}")
```

**Issue: Incorrect field values**
```python
# Debug confidence factors
from pipeline.confidence import ConfidenceManager

manager = ConfidenceManager()
scored = manager.score_extraction(extraction_result, ocr_result)

# Check factor breakdown
for field in ['date', 'total']:
    factors = scored[field]['confidence_factors']
    print(f"{field} factors: {factors}")
```

---

## Performance Profiling

### Time Profiling

```python
import cProfile
import pstats

# Profile function
profiler = cProfile.Profile()
profiler.enable()

result = processor.process_document('image.jpg')

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def process_batch(images):
    processor = DocumentProcessor()
    return processor.process_batch(images)

# Run with: python -m memory_profiler script.py
```

### Line Profiling

```python
from line_profiler import LineProfiler

profiler = LineProfiler()
profiler.add_function(processor.process_document)
profiler.enable()

result = processor.process_document('image.jpg')

profiler.disable()
profiler.print_stats()
```

---

## Contributing

### Workflow

1. **Fork and clone**
2. **Create feature branch**: `git checkout -b feature/my-feature`
3. **Make changes** with tests
4. **Run tests**: `python tests/run_tests.py`
5. **Format code**: `black .`
6. **Commit**: `git commit -m "Add feature X"`
7. **Push**: `git push origin feature/my-feature`
8. **Create pull request**

### Commit Messages

Follow conventional commits:

```
feat: Add company name extraction
fix: Correct date parsing for DD.MM.YYYY format
docs: Update API reference for new extractor
test: Add tests for confidence calibration
refactor: Simplify OCR manager initialization
perf: Optimize pattern matching in extractor
```

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted with Black
- [ ] All tests passing
- [ ] No linting errors
- [ ] CHANGELOG updated

### Code Review

Reviewers check for:
- Code quality and style
- Test coverage
- Documentation
- Performance implications
- Security considerations

---

## Best Practices

1. **Write tests first** (TDD when possible)
2. **Keep functions small** (<50 lines)
3. **Use type hints** everywhere
4. **Document public APIs** thoroughly
5. **Log important operations** with context
6. **Handle errors gracefully**
7. **Optimize only when needed** (profile first)
8. **Review your own code** before submitting

---

**Happy coding!** 🚀

For questions, check the [FAQ](faq.md) or create an issue.
