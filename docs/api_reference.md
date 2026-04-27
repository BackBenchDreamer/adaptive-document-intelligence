# API Reference

Complete API documentation for the Adaptive Document Intelligence System.

## Table of Contents

1. [Core Modules](#core-modules)
2. [Pipeline Modules](#pipeline-modules)
3. [Data Modules](#data-modules)
4. [Evaluation Modules](#evaluation-modules)

---

## Core Modules

### core.config

Central configuration management for the system.

#### `Config` Class

**Purpose:** Centralized configuration with environment-safe defaults.

**Key Attributes:**

```python
# Project Structure
Config.PROJECT_ROOT: Path              # Auto-detected project root
Config.OUTPUT_BASE_PATH: Path          # Base output directory

# Dataset Paths
Config.SROIE_BASE_PATH: Path          # SROIE2019 dataset location
Config.TRAIN_IMG_PATH: Path           # Training images
Config.TRAIN_ENTITIES_PATH: Path      # Training ground truth

# OCR Settings
Config.OCR_ENGINE: str                # 'paddleocr' or 'tesseract'
Config.PADDLEOCR_USE_GPU: bool        # Enable GPU for PaddleOCR
Config.TESSERACT_CMD: str             # Tesseract executable path

# Logging
Config.LOG_LEVEL: str                 # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
Config.LOG_FORMAT_JSON: bool          # Use JSON log format
Config.LOG_FILE_PATH: Path            # Log file location

# System Settings
Config.ENABLE_OCR_CACHE: bool         # Enable OCR result caching
Config.MAX_WORKERS: int               # Parallel processing workers
```

**Methods:**

```python
@classmethod
def ensure_directories() -> None:
    """Create all necessary output directories."""
    
@classmethod
def validate_dataset_paths() -> bool:
    """
    Validate that required dataset paths exist.
    
    Returns:
        bool: True if all paths exist
    """
    
@classmethod
def get_config_summary() -> dict:
    """
    Get configuration summary.
    
    Returns:
        dict: Key configuration values
    """
    
@classmethod
def override_from_env() -> None:
    """Override configuration from environment variables."""
```

**Environment Variables:**

- `ADI_OCR_ENGINE`: OCR engine ('paddleocr' or 'tesseract')
- `ADI_LOG_LEVEL`: Logging level
- `ADI_USE_GPU`: Enable GPU for PaddleOCR
- `ADI_DATASET_PATH`: Override dataset path
- `TESSERACT_CMD`: Tesseract executable path

**Example:**

```python
from core.config import Config

# Ensure directories exist
Config.ensure_directories()

# Validate dataset
if Config.validate_dataset_paths():
    print("Dataset ready")

# Get summary
summary = Config.get_config_summary()
print(f"OCR Engine: {summary['ocr_engine']}")
```

### core.logging_config

Structured logging system with JSON format support.

#### Functions

```python
def setup_logging(
    log_level: str = None,
    log_to_console: bool = True,
    log_to_file: bool = True
) -> None:
    """
    Initialize logging system.
    
    Args:
        log_level: Override default log level
        log_to_console: Enable console logging
        log_to_file: Enable file logging
    """

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """

@contextmanager
def log_performance(logger: logging.Logger, operation: str):
    """
    Context manager for performance logging.
    
    Args:
        logger: Logger instance
        operation: Operation description
        
    Example:
        with log_performance(logger, "OCR processing"):
            result = ocr.extract_text(image)
    """
```

**Example:**

```python
from core.logging_config import setup_logging, get_logger, log_performance

# Initialize logging
setup_logging()

# Get logger
logger = get_logger(__name__)

# Log messages
logger.info("Processing started")
logger.error("Error occurred", extra={"error_code": 500})

# Performance tracking
with log_performance(logger, "Document processing"):
    result = process_document(image)
```

### core.utils

Utility functions for file operations and common tasks.

#### Functions

```python
def read_json_file(file_path: str) -> dict:
    """
    Read JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        dict: Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If invalid JSON
    """

def write_json_file(file_path: str, data: dict, indent: int = 2) -> None:
    """
    Write data to JSON file.
    
    Args:
        file_path: Output file path
        data: Data to write
        indent: JSON indentation
    """

def ensure_path_exists(path: Path, is_file: bool = False) -> None:
    """
    Ensure path exists, creating directories if needed.
    
    Args:
        path: Path to ensure
        is_file: True if path is a file (creates parent dir)
    """

def compute_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    Compute file hash.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha256')
        
    Returns:
        str: Hex digest of file hash
    """
```

---

## Pipeline Modules

### pipeline.ocr

OCR text extraction with multiple engine support.

#### `OCREngine` (Abstract Base Class)

```python
class OCREngine(ABC):
    @abstractmethod
    def extract_text(self, image_path: str) -> Dict:
        """
        Extract text from image.
        
        Returns:
            {
                'text': str,
                'confidence': float,
                'engine': str,
                'processing_time': float,
                'metadata': dict
            }
        """
        
    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available."""
```

#### `PaddleOCREngine`

```python
class PaddleOCREngine(OCREngine):
    def __init__(
        self,
        lang: str = 'en',
        use_gpu: bool = False,
        use_angle_cls: bool = True,
        det_db_thresh: float = 0.3,
        det_db_box_thresh: float = 0.5
    ):
        """
        Initialize PaddleOCR engine.
        
        Args:
            lang: Language code
            use_gpu: Enable GPU acceleration
            use_angle_cls: Enable text orientation detection
            det_db_thresh: Detection threshold
            det_db_box_thresh: Box threshold
        """
```

#### `TesseractEngine`

```python
class TesseractEngine(OCREngine):
    def __init__(
        self,
        lang: str = 'eng',
        config: str = '--oem 3 --psm 6'
    ):
        """
        Initialize Tesseract engine.
        
        Args:
            lang: Language code
            config: Tesseract configuration string
        """
```

#### `OCRManager`

**Purpose:** Manages OCR engines with automatic fallback and caching.

```python
class OCRManager:
    def __init__(
        self,
        preferred_engine: str = 'paddleocr',
        enable_cache: bool = True
    ):
        """
        Initialize OCR manager.
        
        Args:
            preferred_engine: 'paddleocr' or 'tesseract'
            enable_cache: Enable result caching
        """
    
    def extract_text(
        self,
        image_path: str,
        use_cache: bool = True,
        preprocess: bool = False
    ) -> Dict:
        """
        Extract text with automatic fallback.
        
        Args:
            image_path: Path to image
            use_cache: Use cached results
            preprocess: Apply image preprocessing
            
        Returns:
            {
                'text': str,
                'confidence': float,
                'engine': str,
                'processing_time': float,
                'metadata': dict
            }
        """
    
    def get_available_engines(self) -> List[str]:
        """Get list of available OCR engines."""
    
    def clear_cache(self) -> int:
        """
        Clear OCR result cache.
        
        Returns:
            int: Number of cache files deleted
        """
```

**Example:**

```python
from pipeline.ocr import OCRManager

# Initialize manager
manager = OCRManager(
    preferred_engine='tesseract',
    enable_cache=True
)

# Check available engines
print(f"Available: {manager.get_available_engines()}")

# Extract text
result = manager.extract_text('receipt.jpg')
print(f"Text: {result['text']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Engine: {result['engine']}")
```

#### Helper Functions

```python
def preprocess_image(
    image_path: str,
    output_path: Optional[str] = None
) -> str:
    """
    Apply preprocessing to improve OCR accuracy.
    
    Operations:
    - Grayscale conversion
    - Denoising
    - Contrast enhancement
    
    Args:
        image_path: Input image path
        output_path: Output path (temp file if None)
        
    Returns:
        str: Path to preprocessed image
    """
```

### pipeline.extractor

Field extraction using heuristic-based methods.

#### `FieldExtractor` (Abstract Base Class)

```python
class FieldExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> Dict:
        """
        Extract field from text.
        
        Returns:
            {
                'value': Any,
                'confidence': float,
                'candidates': List,
                'method': str,
                'metadata': dict
            }
        """
```

#### `DateExtractor`

```python
class DateExtractor(FieldExtractor):
    """
    Extract date from OCR text.
    
    Supported formats:
    - DD/MM/YYYY, MM/DD/YYYY
    - YYYY-MM-DD
    - DD Mon YYYY, Mon DD YYYY
    - DDMMYYYY, YYYYMMDD
    """
    
    def extract(self, text: str) -> Dict:
        """
        Extract date from text.
        
        Returns:
            {
                'value': str,  # ISO format (YYYY-MM-DD) or None
                'confidence': float,
                'raw_value': str,
                'candidates': List,
                'method': str,
                'metadata': dict
            }
        """
```

#### `TotalExtractor`

```python
class TotalExtractor(FieldExtractor):
    """
    Extract total amount from OCR text.
    
    Handles:
    - Currency symbols ($, €, £, ¥, ₹)
    - Thousands separators
    - Decimal amounts
    - Subtotal vs total disambiguation
    """
    
    def extract(self, text: str) -> Dict:
        """
        Extract total amount.
        
        Returns:
            {
                'value': float,  # Amount or None
                'confidence': float,
                'raw_value': str,
                'candidates': List,
                'method': str,
                'metadata': dict
            }
        """
```

#### `InvoiceNumberExtractor`

```python
class InvoiceNumberExtractor(FieldExtractor):
    """
    Extract invoice/receipt number.
    
    Patterns:
    - INV-12345
    - #123456
    - Receipt: 789012
    - Alphanumeric codes
    """
    
    def extract(self, text: str) -> Dict:
        """
        Extract invoice number.
        
        Returns:
            {
                'value': str,  # Invoice number or None
                'confidence': float,
                'raw_value': str,
                'candidates': List,
                'method': str,
                'metadata': dict
            }
        """
```

#### `ExtractionManager`

```python
class ExtractionManager:
    """Manages all field extractors."""
    
    def __init__(self):
        """Initialize all extractors."""
    
    def extract_fields(self, ocr_result: Dict) -> Dict:
        """
        Extract all fields from OCR result.
        
        Args:
            ocr_result: Output from OCR module
            
        Returns:
            {
                'date': {...},
                'total': {...},
                'invoice_number': {...},
                'metadata': {
                    'ocr_confidence': float,
                    'extraction_time': float,
                    'text_length': int,
                    'candidates_considered': dict
                }
            }
        """
```

**Example:**

```python
from pipeline.extractor import ExtractionManager

# Initialize manager
extractor = ExtractionManager()

# Extract fields from OCR result
ocr_result = {'text': 'Receipt text...', 'confidence': 0.9}
fields = extractor.extract_fields(ocr_result)

print(f"Date: {fields['date']['value']}")
print(f"Total: ${fields['total']['value']:.2f}")
print(f"Invoice: {fields['invoice_number']['value']}")
```

### pipeline.confidence

Multi-factor confidence scoring system.

#### `ConfidenceScorer` (Abstract Base Class)

```python
class ConfidenceScorer(ABC):
    @abstractmethod
    def calculate_confidence(
        self,
        extraction_result: Dict,
        ocr_result: Dict,
        field_name: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate confidence score.
        
        Returns:
            Tuple of (confidence, factor_breakdown)
        """
```

#### `MultiFactorConfidenceScorer`

```python
class MultiFactorConfidenceScorer(ConfidenceScorer):
    """
    Calculate confidence using multiple factors.
    
    Factors:
    - Extraction confidence (40%)
    - OCR quality (30%)
    - Value validity (20%)
    - Pattern strength (10%)
    """
    
    def calculate_confidence(
        self,
        extraction_result: Dict,
        ocr_result: Dict,
        field_name: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate multi-factor confidence.
        
        Returns:
            (final_confidence, {
                'extraction': float,
                'ocr_quality': float,
                'validity': float,
                'pattern': float
            })
        """
```

#### `ConfidenceCalibrator`

```python
class ConfidenceCalibrator:
    """Calibrate confidence scores using validation data."""
    
    def fit(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ):
        """
        Fit calibrator using validation data.
        
        Args:
            predictions: Extraction results with confidence
            ground_truth: Ground truth values
        """
    
    def calibrate(
        self,
        raw_confidence: float,
        field_name: str
    ) -> float:
        """
        Calibrate a raw confidence score.
        
        Args:
            raw_confidence: Uncalibrated score [0, 1]
            field_name: Field type
            
        Returns:
            float: Calibrated confidence [0, 1]
        """
```

#### `ConfidenceManager`

```python
class ConfidenceManager:
    """Manages confidence scoring for all fields."""
    
    def __init__(
        self,
        use_calibration: bool = False,
        calibrator: Optional[ConfidenceCalibrator] = None
    ):
        """
        Initialize confidence manager.
        
        Args:
            use_calibration: Apply calibration
            calibrator: Pre-trained calibrator
        """
    
    def score_extraction(
        self,
        extraction_results: Dict,
        ocr_result: Dict
    ) -> Dict:
        """
        Score all extracted fields.
        
        Returns:
            {
                'date': {
                    'value': ...,
                    'confidence': float,
                    'raw_confidence': float,
                    'confidence_factors': dict
                },
                'total': {...},
                'invoice_number': {...},
                'metadata': {
                    'calibration_applied': bool,
                    'scoring_time': float
                }
            }
        """
```

**Example:**

```python
from pipeline.confidence import ConfidenceManager

# Initialize manager
confidence_mgr = ConfidenceManager(use_calibration=False)

# Score extraction results
scored = confidence_mgr.score_extraction(
    extraction_results,
    ocr_result
)

print(f"Date confidence: {scored['date']['confidence']:.2f}")
print(f"Factors: {scored['date']['confidence_factors']}")
```

### pipeline.pipeline

End-to-end pipeline orchestration.

#### `DocumentProcessor`

**Purpose:** Complete document processing pipeline.

```python
class DocumentProcessor:
    def __init__(
        self,
        ocr_engine: str = 'tesseract',
        use_preprocessing: bool = True,
        use_cache: bool = True,
        use_calibration: bool = False
    ):
        """
        Initialize document processor.
        
        Args:
            ocr_engine: 'paddleocr' or 'tesseract'
            use_preprocessing: Apply image preprocessing
            use_cache: Cache OCR results
            use_calibration: Use calibrated confidence
        """
    
    def process_document(
        self,
        image_path: str,
        return_intermediate: bool = False
    ) -> Dict:
        """
        Process a single document.
        
        Pipeline stages:
        1. OCR: Extract text
        2. Extraction: Extract fields
        3. Confidence: Score quality
        4. Packaging: Format result
        
        Returns:
            {
                'image_path': str,
                'image_id': str,
                'fields': {
                    'date': {'value': str, 'confidence': float, 'raw_value': str},
                    'total': {'value': float, 'confidence': float, 'raw_value': str},
                    'invoice_number': {'value': str, 'confidence': float, 'raw_value': str}
                },
                'metadata': {
                    'processing_time': float,
                    'ocr_engine': str,
                    'ocr_confidence': float,
                    'success': bool,
                    'timestamp': str
                }
            }
        """
    
    def process_batch(
        self,
        image_paths: List[str],
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Process multiple documents sequentially.
        
        Args:
            image_paths: List of image paths
            show_progress: Show progress bar
            
        Returns:
            List of processing results
        """
    
    def get_statistics(self, results: List[Dict]) -> Dict:
        """
        Calculate statistics from batch results.
        
        Returns:
            {
                'total_processed': int,
                'successful': int,
                'failed': int,
                'avg_processing_time': float,
                'avg_confidence': dict,
                'extraction_rate': dict
            }
        """
```

**Example:**

```python
from pipeline import DocumentProcessor

# Initialize processor
processor = DocumentProcessor(ocr_engine='tesseract')

# Process single document
result = processor.process_document('receipt.jpg')
print(f"Date: {result['fields']['date']['value']}")
print(f"Total: ${result['fields']['total']['value']:.2f}")

# Process batch
results = processor.process_batch(['img1.jpg', 'img2.jpg'])
stats = processor.get_statistics(results)
print(f"Success rate: {stats['successful']}/{stats['total_processed']}")
```

#### `BatchProcessor`

```python
class BatchProcessor:
    """Efficient batch processing with optional parallelization."""
    
    def __init__(
        self,
        processor: DocumentProcessor,
        max_workers: int = 4,
        use_parallel: bool = False
    ):
        """
        Initialize batch processor.
        
        Args:
            processor: DocumentProcessor instance
            max_workers: Max parallel workers
            use_parallel: Enable parallel processing
        """
    
    def process_directory(
        self,
        directory: str,
        pattern: str = '*.jpg',
        limit: Optional[int] = None
    ) -> Dict:
        """
        Process all images in directory.
        
        Args:
            directory: Directory path
            pattern: File pattern (e.g., '*.jpg')
            limit: Max files to process
            
        Returns:
            {
                'results': List[Dict],
                'statistics': Dict,
                'errors': List[Dict]
            }
        """
```

#### `PipelineManager`

```python
class PipelineManager:
    """High-level pipeline management."""
    
    @staticmethod
    def create_processor(config: Optional[Dict] = None) -> DocumentProcessor:
        """Create processor with configuration."""
    
    @staticmethod
    def process_sroie_dataset(
        split: str = 'train',
        limit: Optional[int] = None,
        compare_ground_truth: bool = True,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Process SROIE dataset.
        
        Returns:
            {
                'results': List[Dict],
                'statistics': Dict,
                'accuracy': Dict  # If compare_ground_truth=True
            }
        """
    
    @staticmethod
    def save_results(
        results: List[Dict],
        output_path: str,
        format: str = 'json'
    ):
        """
        Save results to file.
        
        Args:
            results: Processing results
            output_path: Output file path
            format: 'json' or 'csv'
        """
```

#### Convenience Function

```python
def process_image(image_path: str, **kwargs) -> Dict:
    """
    Quick convenience function to process a single image.
    
    Args:
        image_path: Path to image
        **kwargs: Additional arguments for DocumentProcessor
        
    Returns:
        Processing result
    """
```

**Example:**

```python
from pipeline import process_image

# Quick processing
result = process_image('receipt.jpg', ocr_engine='tesseract')
print(result['fields']['total']['value'])
```

---

## Data Modules

### tests.data.sroie_loader

SROIE2019 dataset loader.

#### `SROIEDataLoader`

```python
class SROIEDataLoader:
    """Load and parse SROIE2019 dataset."""
    
    def __init__(self, split: str = 'train'):
        """
        Initialize loader.
        
        Args:
            split: 'train' or 'test'
        """
    
    def load_dataset(self) -> List[Dict]:
        """
        Load all samples from dataset.
        
        Returns:
            List of samples with structure:
            {
                'image_id': str,
                'image_path': str,
                'entities': {
                    'company': str,
                    'date': str,  # ISO format
                    'address': str,
                    'total': float
                },
                'has_required_fields': bool
            }
        """
    
    def load_single_sample(self, image_id: str) -> Optional[Dict]:
        """Load a single sample by ID."""
    
    def get_statistics(self) -> Dict:
        """
        Get dataset statistics.
        
        Returns:
            {
                'total_samples': int,
                'valid_samples': int,
                'date_range': Tuple[str, str],
                'total_range': Tuple[float, float]
            }
        """
```

**Example:**

```python
from tests.data import SROIEDataLoader

# Load training data
loader = SROIEDataLoader(split='train')
samples = loader.load_dataset()

print(f"Loaded {len(samples)} samples")

# Get statistics
stats = loader.get_statistics()
print(f"Valid: {stats['valid_samples']}/{stats['total_samples']}")
```

---

## Evaluation Modules

### tests.metrics.evaluation

System evaluation and metrics calculation.

#### `DocumentEvaluator`

```python
class DocumentEvaluator:
    """Evaluate document processing results."""
    
    def evaluate_predictions(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict:
        """
        Evaluate predictions against ground truth.
        
        Returns:
            {
                'date': {
                    'accuracy': float,
                    'precision': float,
                    'recall': float,
                    'f1_score': float
                },
                'total': {...},
                'invoice_number': {...},
                'overall_accuracy': float
            }
        """
```

### tests.analysis.error_analysis

Error analysis and categorization.

#### `ErrorAnalyzer`

```python
class ErrorAnalyzer:
    """Analyze extraction errors."""
    
    def analyze_errors(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ) -> Dict:
        """
        Analyze and categorize errors.
        
        Returns:
            {
                'total_errors': int,
                'error_categories': {
                    'ocr_errors': int,
                    'format_errors': int,
                    'missing_fields': int
                },
                'error_examples': List[Dict]
            }
        """
```

---

## Type Definitions

### Common Return Types

**OCR Result:**
```python
{
    'text': str,              # Extracted text
    'confidence': float,      # Overall confidence [0,1]
    'engine': str,            # Engine name
    'processing_time': float, # Time in seconds
    'metadata': dict          # Engine-specific metadata
}
```

**Extraction Result:**
```python
{
    'value': Any,           # Extracted value (or None)
    'confidence': float,    # Extraction confidence [0,1]
    'raw_value': str,       # Original text
    'candidates': List,     # All candidates considered
    'method': str,          # Extraction method used
    'metadata': dict        # Additional info
}
```

**Processing Result:**
```python
{
    'image_path': str,
    'image_id': str,
    'fields': {
        'date': {'value': str, 'confidence': float, 'raw_value': str},
        'total': {'value': float, 'confidence': float, 'raw_value': str},
        'invoice_number': {'value': str, 'confidence': float, 'raw_value': str}
    },
    'metadata': {
        'processing_time': float,
        'ocr_engine': str,
        'ocr_confidence': float,
        'success': bool,
        'timestamp': str
    }
}
```

---

## Error Handling

All modules use consistent error handling:

- **Graceful degradation**: System continues on non-fatal errors
- **Detailed logging**: All errors logged with context
- **Error results**: Failed operations return structured error results
- **Exception types**: Standard Python exceptions (FileNotFoundError, ValueError, etc.)

**Example Error Handling:**

```python
from pipeline import DocumentProcessor

processor = DocumentProcessor()

try:
    result = processor.process_document('receipt.jpg')
    
    if result['metadata']['success']:
        # Process successful result
        process_result(result)
    else:
        # Handle processing failure
        error = result['metadata']['error']
        logger.error(f"Processing failed: {error}")
        
except FileNotFoundError:
    logger.error("Image file not found")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

---

## Performance Considerations

### Caching

OCR results are cached by default:

```python
# Enable caching (default)
processor = DocumentProcessor(use_cache=True)

# Disable caching
processor = DocumentProcessor(use_cache=False)

# Clear cache
from pipeline.ocr import OCRManager
manager = OCRManager()
deleted = manager.clear_cache()
print(f"Cleared {deleted} cache files")
```

### Parallel Processing

For batch processing:

```python
from pipeline import BatchProcessor, DocumentProcessor

processor = DocumentProcessor()
batch = BatchProcessor(
    processor,
    max_workers=4,
    use_parallel=True
)

results = batch.process_directory('images/')
```

### Memory Management

For large batches, process in chunks:

```python
chunk_size = 100
for i in range(0, len(files), chunk_size):
    chunk = files[i:i+chunk_size]
    results = processor.process_batch(chunk)
    save_results(results)
    del results  # Free memory
```

---

## See Also

- [User Guide](user_guide.md) - Usage examples and best practices
- [Architecture](architecture.md) - System design and architecture
- [Development Guide](development.md) - Contributing and extending

---

**Last Updated:** 2024-01-27  
**Version:** 1.0.0