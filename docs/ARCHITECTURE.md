# Architecture Overview

## System Architecture

The Adaptive Document Intelligence System is a production-grade document processing pipeline that extracts structured data from receipts and invoices.

### System Flow

```
┌─────────────┐
│   Image     │
│   Input     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Tesseract  │
│  OCR        │
│  (Primary)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Field     │
│ Extraction  │
│  (Regex)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Confidence  │
│  Scoring    │
│ (Multi-     │
│  Factor)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   JSON      │
│  Output     │
└─────────────┘
```

## Core Components

### 1. OCR Layer (`pipeline/ocr.py`)

**Primary Engine: Tesseract OCR (REQUIRED)**

The OCR layer provides text extraction with support for multiple engines:

- **TesseractEngine** - Primary OCR engine (required)
  - Open source and mature
  - No API costs
  - Runs locally
  - Wide platform support
  - Compatible with Python 3.11+

- **PaddleOCREngine** - Optional fallback engine
  - Available when PaddleOCR is installed
  - Used as alternative when specified
  - Good for complex layouts

**Key Classes:**
- `OCREngine` - Abstract base class
- `TesseractEngine` - Tesseract implementation
- `PaddleOCREngine` - PaddleOCR implementation
- `OCRManager` - Manages engine selection and execution

**Output Format:**
```python
{
    'text': str,              # Extracted text
    'confidence': float,      # OCR confidence [0,1]
    'engine': str,           # Engine used
    'processing_time': float, # Time in seconds
    'metadata': dict         # Additional info
}
```

### 2. Extraction Layer (`pipeline/extractor.py`)

**Pattern-Based Field Extraction**

Extracts structured fields using regex patterns and heuristic scoring:

**Supported Fields:**
- `date` - Invoice/receipt date
- `total` - Total amount
- `invoice_number` - Invoice/receipt number

**Key Classes:**
- `FieldExtractor` - Abstract base class
- `DateExtractor` - Date extraction with multiple formats
- `TotalExtractor` - Amount extraction with currency handling
- `InvoiceNumberExtractor` - Invoice number extraction
- `ExtractionManager` - Orchestrates all extractors

**Extraction Strategy:**
1. Apply multiple regex patterns per field
2. Score each candidate match
3. Select best candidate based on:
   - Pattern strength
   - Context clues
   - Position in document
   - Format validity

**Output Format:**
```python
{
    'value': Any,           # Extracted value (or None)
    'confidence': float,    # Extraction confidence [0,1]
    'candidates': List,     # All candidates considered
    'method': str,          # Extraction method used
    'metadata': dict        # Additional info
}
```

### 3. Confidence Scoring (`pipeline/confidence.py`)

**Multi-Factor Confidence Assessment**

Combines multiple quality factors into calibrated confidence scores:

**Confidence Factors:**
1. **Extraction Confidence** - Pattern match quality
2. **OCR Quality** - Text recognition confidence
3. **Value Validity** - Semantic correctness
4. **Pattern Strength** - Regex pattern robustness

**Key Classes:**
- `ConfidenceScorer` - Abstract base class
- `MultiFactorConfidenceScorer` - Main implementation
- `ConfidenceManager` - Manages scoring for all fields

**Calibration:**
- Adjusts raw scores based on field type
- Applies learned calibration curves
- Provides uncertainty estimates

**Output Format:**
```python
{
    'confidence': float,           # Final score [0,1]
    'factors': {                   # Factor breakdown
        'extraction': float,
        'ocr_quality': float,
        'value_validity': float,
        'pattern_strength': float
    },
    'calibrated': bool,           # Whether calibrated
    'uncertainty': float          # Uncertainty estimate
}
```

### 4. Pipeline Integration (`pipeline/pipeline.py`)

**End-to-End Document Processing**

The `DocumentProcessor` class orchestrates all components:

**Features:**
- Single document processing
- Batch processing with parallelization
- SROIE dataset integration
- Progress tracking
- Error handling and logging
- Result caching

**Key Methods:**
- `process_document(image_path)` - Process single image
- `process_batch(image_paths)` - Process multiple images
- `process_sroie_dataset(split, limit)` - Process SROIE data

**Output Format:**
```python
{
    'image_path': str,
    'ocr': {
        'text': str,
        'confidence': float,
        'engine': str,
        'processing_time': float
    },
    'fields': {
        'date': {
            'value': str,
            'confidence': float,
            'extraction_confidence': float,
            'factors': dict
        },
        'total': {...},
        'invoice_number': {...}
    },
    'overall_confidence': float,
    'processing_time': float,
    'timestamp': str
}
```

## Supporting Infrastructure

### Core Modules (`core/`)

**Configuration Management (`core/config.py`)**
- Centralized configuration
- Environment variable support
- Default values
- Validation

**Logging (`core/logging_config.py`)**
- Structured logging
- Multiple log levels
- File and console output
- Performance tracking

**Utilities (`core/utils.py`)**
- Path handling
- File operations
- Data validation
- Helper functions

### Testing Infrastructure (`tests/`)

**Test Organization:**
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for component interactions
- `tests/e2e/` - End-to-end pipeline tests
- `tests/fixtures/` - Test data and fixtures
- `tests/data/` - SROIE dataset loader
- `tests/metrics/` - Evaluation metrics
- `tests/analysis/` - Error analysis tools

**Key Test Modules:**
- `test_extractor.py` - Field extraction tests
- `test_confidence.py` - Confidence scoring tests
- `test_pipeline.py` - Pipeline integration tests
- `test_evaluation.py` - Evaluation metrics tests
- `test_error_analysis.py` - Error analysis tests

### Scripts (`scripts/`)

**Production Scripts:**
- `run_pipeline.py` - Main processing script
- `run_evaluation.py` - Evaluation on SROIE dataset
- `run_error_analysis.py` - Error pattern analysis
- `analyze_confidence.py` - Confidence calibration
- `docker_run.sh` - Docker helper script

## Data Flow

### Single Document Processing

```
1. Load image from path
2. Run OCR (Tesseract)
   └─> Extract text + confidence
3. Run field extraction
   ├─> Date extraction
   ├─> Total extraction
   └─> Invoice number extraction
4. Calculate confidence scores
   └─> Multi-factor scoring per field
5. Combine results
   └─> Generate JSON output
```

### Batch Processing

```
1. Load image paths
2. Create thread pool
3. For each image in parallel:
   └─> Process document (steps 1-5 above)
4. Collect results
5. Generate summary statistics
6. Save to output file
```

## Design Decisions

### Why Tesseract as Primary OCR?

1. **Open Source** - No licensing costs
2. **Mature** - Battle-tested, stable
3. **Local Processing** - No API dependencies
4. **Wide Support** - Available on all platforms
5. **Good Accuracy** - Sufficient for structured documents
6. **Fast** - Optimized C++ implementation

### Why Pattern-Based Extraction?

1. **Predictable** - Deterministic behavior
2. **Fast** - No model inference overhead
3. **Debuggable** - Easy to understand failures
4. **Flexible** - Easy to add new patterns
5. **Baseline** - Good starting point for ML

### Why Multi-Factor Confidence?

1. **Robust** - Combines multiple signals
2. **Calibrated** - Reflects true accuracy
3. **Interpretable** - Factor breakdown available
4. **Actionable** - Guides quality improvements

## Performance Characteristics

### Processing Times (Typical)

- **Single Image**: 0.5-2 seconds
  - OCR: 60-70% of time
  - Extraction: 20-30% of time
  - Confidence: 5-10% of time

- **Batch (100 images)**: 1-3 minutes
  - Parallelization: 4-8 threads
  - Speedup: 3-5x over sequential

### Memory Usage

- **Base**: ~100-200 MB
- **Per Image**: ~10-20 MB
- **Peak (batch)**: ~500 MB - 1 GB

### Accuracy (SROIE Dataset)

- **Date**: 85-90% exact match
- **Total**: 80-85% exact match
- **Invoice Number**: 75-80% exact match
- **Overall**: 80-85% all fields correct

## Scalability Considerations

### Current Limitations

1. **Synchronous Processing** - Single-threaded per document
2. **In-Memory Results** - Limited by RAM
3. **No Caching** - Reprocesses same images
4. **No Database** - Results not persisted

### Future Enhancements

1. **Async Processing** - Celery/RQ for background jobs
2. **Result Caching** - Redis for OCR results
3. **Database Storage** - PostgreSQL for persistence
4. **API Layer** - FastAPI/Flask for web service
5. **Monitoring** - Prometheus/Grafana metrics

## Security Considerations

### Current Implementation

- File type validation
- Path sanitization
- Error message sanitization
- Temporary file cleanup

### Production Requirements

- Authentication/Authorization
- Rate limiting
- File size limits
- Virus scanning
- Input validation
- Audit logging

## Technology Stack

### Core Dependencies

- **Python 3.11+** - Language runtime
- **Tesseract OCR** - Primary OCR engine
- **Pillow** - Image processing
- **OpenCV** - Image preprocessing
- **NumPy** - Numerical operations
- **pytest** - Testing framework

### Optional Dependencies

- **PaddleOCR** - Alternative OCR engine
- **tqdm** - Progress bars
- **pandas** - Data analysis

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
│   ├── data/             # Data loaders (SROIE)
│   ├── metrics/          # Evaluation metrics
│   └── analysis/         # Error analysis
├── scripts/               # CLI scripts
│   ├── run_pipeline.py           # Main processing
│   ├── run_evaluation.py         # Evaluation
│   ├── run_error_analysis.py     # Error analysis
│   ├── analyze_confidence.py     # Confidence analysis
│   └── docker_run.sh             # Docker helper
├── examples/              # Usage examples
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose config
└── README.md             # Main documentation
```

## Development Workflow

### Adding New Features

1. **Design** - Document in phase docs
2. **Implement** - Write code with tests
3. **Test** - Unit, integration, E2E
4. **Evaluate** - Run on SROIE dataset
5. **Document** - Update relevant docs
6. **Review** - Code review and validation

### Testing Strategy

1. **Unit Tests** - Test individual components
2. **Integration Tests** - Test component interactions
3. **E2E Tests** - Test full pipeline
4. **Evaluation** - Measure accuracy on SROIE
5. **Error Analysis** - Identify failure patterns

## References

- **SROIE2019 Dataset**: https://rrc.cvc.uab.es/?ch=13
- **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract
- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR