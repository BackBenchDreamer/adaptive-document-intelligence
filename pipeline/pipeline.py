"""
Pipeline Integration Module for Adaptive Document Intelligence System.

This module orchestrates all components (OCR, extraction, confidence scoring)
into a unified end-to-end workflow for document processing.

Author: Adaptive Document Intelligence System
Phase: 6 - Pipeline Integration
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Optional progress bar support
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Fallback: simple iterator wrapper
    def tqdm(iterable, **kwargs):
        """Fallback tqdm that just returns the iterable."""
        desc = kwargs.get('desc', 'Processing')
        total = len(iterable) if hasattr(iterable, '__len__') else '?'
        print(f"{desc}: 0/{total}", end='', flush=True)
        for i, item in enumerate(iterable, 1):
            yield item
            print(f"\r{desc}: {i}/{total}", end='', flush=True)
        print()  # New line at end

from core.config import Config
from core.logging_config import get_logger
from core.utils import ensure_path_exists
from pipeline.ocr import OCRManager
from pipeline.extractor import ExtractionManager
from pipeline.confidence import ConfidenceManager
from tests.data.sroie_loader import SROIEDataLoader

logger = get_logger(__name__)


class DocumentProcessor:
    """
    End-to-end document processing pipeline.
    
    Orchestrates OCR, extraction, and confidence scoring to transform
    document images into structured, validated data.
    
    Features:
    - Configurable OCR engine (PaddleOCR/Tesseract)
    - Optional preprocessing and caching
    - Multi-factor confidence scoring
    - Comprehensive error handling
    - Performance tracking
    
    Example:
        >>> processor = DocumentProcessor(ocr_engine='tesseract')
        >>> result = processor.process_document('receipt.jpg')
        >>> print(result['fields']['total']['value'])
        4.95
    """
    
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
            use_calibration: Use calibrated confidence scores
        """
        self.ocr_engine = ocr_engine
        self.use_preprocessing = use_preprocessing
        self.use_cache = use_cache
        self.use_calibration = use_calibration
        
        # Initialize components
        logger.info(f"Initializing DocumentProcessor with engine={ocr_engine}")
        
        self.ocr_manager = OCRManager(
            preferred_engine=ocr_engine,
            enable_cache=use_cache
        )
        
        self.extractor = ExtractionManager()
        
        self.confidence_manager = ConfidenceManager(
            use_calibration=use_calibration
        )
        
        logger.info("DocumentProcessor initialized successfully")
    
    def process_document(
        self,
        image_path: str,
        return_intermediate: bool = False
    ) -> Dict:
        """
        Process a single document through the complete pipeline.
        
        Pipeline stages:
        1. OCR: Extract text from image
        2. Extraction: Extract structured fields
        3. Confidence: Score field quality
        4. Packaging: Format final result
        
        Args:
            image_path: Path to document image
            return_intermediate: Include intermediate results (OCR, extraction)
            
        Returns:
            {
                'image_path': str,
                'image_id': str,
                'fields': {
                    'date': {
                        'value': str,           # ISO format or None
                        'confidence': float,    # [0, 1]
                        'raw_value': str
                    },
                    'total': {
                        'value': float,         # Amount or None
                        'confidence': float,
                        'raw_value': str
                    },
                    'invoice_number': {
                        'value': str,           # Invoice number or None
                        'confidence': float,
                        'raw_value': str
                    }
                },
                'metadata': {
                    'processing_time': float,
                    'ocr_engine': str,
                    'ocr_confidence': float,
                    'success': bool,
                    'timestamp': str,
                    'error': str  # Only if failed
                },
                'intermediate': {  # Only if return_intermediate=True
                    'ocr_result': {...},
                    'extraction_result': {...}
                }
            }
        """
        start_time = time.time()
        image_path = str(image_path)
        image_id = Path(image_path).stem
        
        logger.info(f"Processing document: {image_id}")
        
        try:
            # Stage 1: OCR
            logger.debug(f"Stage 1: OCR for {image_id}")
            ocr_result = self.ocr_manager.extract_text(image_path)
            
            if not ocr_result or not ocr_result.get('text'):
                logger.warning(f"OCR failed or returned empty text for {image_id}")
                return self._create_error_result(
                    image_path,
                    image_id,
                    "OCR failed or returned empty text",
                    start_time
                )
            
            # Stage 2: Field Extraction
            logger.debug(f"Stage 2: Extraction for {image_id}")
            extraction_result = self.extractor.extract_fields(ocr_result)
            
            # Stage 3: Confidence Scoring
            logger.debug(f"Stage 3: Confidence scoring for {image_id}")
            scored_result = self.confidence_manager.score_extraction(
                extraction_result,
                ocr_result
            )
            
            # Stage 4: Package Result
            processing_time = time.time() - start_time
            
            result = {
                'image_path': image_path,
                'image_id': image_id,
                'fields': {
                    'date': {
                        'value': scored_result['date']['value'],
                        'confidence': scored_result['date']['confidence'],
                        'raw_value': scored_result['date'].get('raw_value', '')
                    },
                    'total': {
                        'value': scored_result['total']['value'],
                        'confidence': scored_result['total']['confidence'],
                        'raw_value': scored_result['total'].get('raw_value', '')
                    },
                    'invoice_number': {
                        'value': scored_result['invoice_number']['value'],
                        'confidence': scored_result['invoice_number']['confidence'],
                        'raw_value': scored_result['invoice_number'].get('raw_value', '')
                    }
                },
                'metadata': {
                    'processing_time': processing_time,
                    'ocr_engine': ocr_result.get('engine', self.ocr_engine),
                    'ocr_confidence': ocr_result.get('confidence', 0.0),
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # Add intermediate results if requested
            if return_intermediate:
                result['intermediate'] = {
                    'ocr_result': ocr_result,
                    'extraction_result': extraction_result,
                    'scored_result': scored_result
                }
            
            logger.info(
                f"Successfully processed {image_id} in {processing_time:.3f}s "
                f"(date: {result['fields']['date']['confidence']:.2f}, "
                f"total: {result['fields']['total']['confidence']:.2f}, "
                f"invoice: {result['fields']['invoice_number']['confidence']:.2f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {image_id}: {e}", exc_info=True)
            return self._create_error_result(
                image_path,
                image_id,
                str(e),
                start_time
            )
    
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
            List of processing results (one per image)
        """
        logger.info(f"Processing batch of {len(image_paths)} documents")
        
        results = []
        iterator = tqdm(image_paths, desc="Processing") if show_progress else image_paths
        
        for image_path in iterator:
            result = self.process_document(image_path)
            results.append(result)
        
        logger.info(f"Batch processing complete: {len(results)} documents processed")
        return results
    
    def get_statistics(self, results: List[Dict]) -> Dict:
        """
        Calculate statistics from batch processing results.
        
        Args:
            results: List of processing results
            
        Returns:
            {
                'total_processed': int,
                'successful': int,
                'failed': int,
                'avg_processing_time': float,
                'avg_confidence': {
                    'date': float,
                    'total': float,
                    'invoice_number': float
                },
                'extraction_rate': {
                    'date': float,
                    'total': float,
                    'invoice_number': float
                }
            }
        """
        if not results:
            return {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'avg_processing_time': 0.0,
                'avg_confidence': {'date': 0.0, 'total': 0.0, 'invoice_number': 0.0},
                'extraction_rate': {'date': 0.0, 'total': 0.0, 'invoice_number': 0.0}
            }
        
        total_processed = len(results)
        successful = sum(1 for r in results if r['metadata']['success'])
        failed = total_processed - successful
        
        # Calculate average processing time
        processing_times = [r['metadata']['processing_time'] for r in results]
        avg_processing_time = sum(processing_times) / len(processing_times)
        
        # Calculate confidence and extraction rates per field
        field_stats = {}
        for field_name in ['date', 'total', 'invoice_number']:
            confidences = []
            extracted_count = 0
            
            for result in results:
                if result['metadata']['success']:
                    field_data = result['fields'][field_name]
                    if field_data['value'] is not None:
                        confidences.append(field_data['confidence'])
                        extracted_count += 1
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            extraction_rate = extracted_count / successful if successful > 0 else 0.0
            
            field_stats[field_name] = {
                'avg_confidence': avg_confidence,
                'extraction_rate': extraction_rate
            }
        
        statistics = {
            'total_processed': total_processed,
            'successful': successful,
            'failed': failed,
            'avg_processing_time': avg_processing_time,
            'avg_confidence': {
                field: field_stats[field]['avg_confidence']
                for field in ['date', 'total', 'invoice_number']
            },
            'extraction_rate': {
                field: field_stats[field]['extraction_rate']
                for field in ['date', 'total', 'invoice_number']
            }
        }
        
        logger.info(f"Statistics calculated: {successful}/{total_processed} successful")
        return statistics
    
    def _create_error_result(
        self,
        image_path: str,
        image_id: str,
        error_message: str,
        start_time: float
    ) -> Dict:
        """Create a standardized error result."""
        return {
            'image_path': image_path,
            'image_id': image_id,
            'fields': {
                'date': {'value': None, 'confidence': 0.0, 'raw_value': ''},
                'total': {'value': None, 'confidence': 0.0, 'raw_value': ''},
                'invoice_number': {'value': None, 'confidence': 0.0, 'raw_value': ''}
            },
            'metadata': {
                'processing_time': time.time() - start_time,
                'ocr_engine': self.ocr_engine,
                'ocr_confidence': 0.0,
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': error_message
            }
        }


class BatchProcessor:
    """
    Efficient batch processing with optional parallel execution.
    
    Features:
    - Sequential or parallel processing
    - Progress tracking
    - Error recovery (continues on failures)
    - Result aggregation
    - Directory scanning
    
    Example:
        >>> processor = DocumentProcessor()
        >>> batch = BatchProcessor(processor, use_parallel=True)
        >>> results = batch.process_directory('images/', limit=100)
    """
    
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
            max_workers: Max parallel workers (if use_parallel=True)
            use_parallel: Enable parallel processing
        """
        self.processor = processor
        self.max_workers = max_workers
        self.use_parallel = use_parallel
        
        logger.info(
            f"BatchProcessor initialized "
            f"(parallel={'enabled' if use_parallel else 'disabled'}, "
            f"workers={max_workers if use_parallel else 1})"
        )
    
    def process_directory(
        self,
        directory: str,
        pattern: str = '*.jpg',
        limit: Optional[int] = None
    ) -> Dict:
        """
        Process all images in a directory.
        
        Args:
            directory: Directory path
            pattern: File pattern (e.g., '*.jpg', '*.png')
            limit: Max files to process (None = all)
            
        Returns:
            {
                'results': List[Dict],      # Processing results
                'statistics': Dict,         # Aggregate statistics
                'errors': List[Dict]        # Error details
            }
        """
        directory_path = Path(directory)
        
        if not directory_path.exists():
            logger.error(f"Directory not found: {directory}")
            return {
                'results': [],
                'statistics': {},
                'errors': [{'error': f"Directory not found: {directory}"}]
            }
        
        # Find all matching images
        image_paths = sorted(directory_path.glob(pattern))
        
        if limit:
            image_paths = image_paths[:limit]
        
        logger.info(f"Found {len(image_paths)} images in {directory}")
        
        if not image_paths:
            logger.warning(f"No images found matching pattern '{pattern}'")
            return {
                'results': [],
                'statistics': {},
                'errors': []
            }
        
        # Process images
        if self.use_parallel:
            results = self._process_parallel(image_paths)
        else:
            results = self.processor.process_batch(
                [str(p) for p in image_paths],
                show_progress=True
            )
        
        # Calculate statistics
        statistics = self.processor.get_statistics(results)
        
        # Extract errors
        errors = [
            {
                'image_id': r['image_id'],
                'error': r['metadata'].get('error', 'Unknown error')
            }
            for r in results
            if not r['metadata']['success']
        ]
        
        return {
            'results': results,
            'statistics': statistics,
            'errors': errors
        }
    
    def _process_parallel(self, image_paths: List[Path]) -> List[Dict]:
        """Process images in parallel using ThreadPoolExecutor."""
        logger.info(f"Processing {len(image_paths)} images in parallel")
        
        results = []
        completed = 0
        total = len(image_paths)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self.processor.process_document, str(path)): path
                for path in image_paths
            }
            
            # Collect results with progress tracking
            if HAS_TQDM:
                pbar = tqdm(total=total, desc="Processing")
            else:
                print(f"Processing: 0/{total}", end='', flush=True)
            
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {path}: {e}")
                    # Create error result
                    results.append({
                        'image_path': str(path),
                        'image_id': path.stem,
                        'fields': {
                            'date': {'value': None, 'confidence': 0.0, 'raw_value': ''},
                            'total': {'value': None, 'confidence': 0.0, 'raw_value': ''},
                            'invoice_number': {'value': None, 'confidence': 0.0, 'raw_value': ''}
                        },
                        'metadata': {
                            'processing_time': 0.0,
                            'ocr_engine': self.processor.ocr_engine,
                            'ocr_confidence': 0.0,
                            'success': False,
                            'timestamp': datetime.now().isoformat(),
                            'error': str(e)
                        }
                    })
                finally:
                    completed += 1
                    if HAS_TQDM:
                        pbar.update(1)
                    else:
                        print(f"\rProcessing: {completed}/{total}", end='', flush=True)
            
            if HAS_TQDM:
                pbar.close()
            else:
                print()  # New line
        
        # Sort results by image_id to maintain order
        results.sort(key=lambda x: x['image_id'])
        
        return results


class PipelineManager:
    """
    High-level pipeline management with convenient methods.
    
    Provides simplified interfaces for common workflows like
    processing SROIE datasets, saving results, and comparing
    with ground truth.
    
    Example:
        >>> # Process SROIE training set
        >>> results = PipelineManager.process_sroie_dataset(
        ...     split='train',
        ...     limit=100,
        ...     compare_ground_truth=True
        ... )
        >>> print(results['accuracy'])
    """
    
    @staticmethod
    def create_processor(config: Optional[Dict] = None) -> DocumentProcessor:
        """
        Create processor with configuration.
        
        Args:
            config: Configuration dict with keys:
                - ocr_engine: 'paddleocr' or 'tesseract'
                - use_preprocessing: bool
                - use_cache: bool
                - use_calibration: bool
                
        Returns:
            Configured DocumentProcessor instance
        """
        if config is None:
            config = {}
        
        return DocumentProcessor(
            ocr_engine=config.get('ocr_engine', 'tesseract'),
            use_preprocessing=config.get('use_preprocessing', True),
            use_cache=config.get('use_cache', True),
            use_calibration=config.get('use_calibration', False)
        )
    
    @staticmethod
    def process_sroie_dataset(
        split: str = 'train',
        limit: Optional[int] = None,
        compare_ground_truth: bool = True,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Process SROIE dataset.
        
        Args:
            split: 'train' or 'test'
            limit: Max samples to process (None = all)
            compare_ground_truth: Compare with ground truth and calculate accuracy
            config: Processor configuration
            
        Returns:
            {
                'results': List[Dict],
                'statistics': Dict,
                'accuracy': Dict  # Only if compare_ground_truth=True
            }
        """
        logger.info(f"Processing SROIE {split} dataset (limit={limit})")
        
        # Load dataset
        loader = SROIEDataLoader(split=split)
        samples = loader.load_dataset()
        
        if limit:
            samples = samples[:limit]
        
        logger.info(f"Loaded {len(samples)} samples from SROIE {split}")
        
        # Create processor
        processor = PipelineManager.create_processor(config)
        
        # Process all images
        image_paths = [sample['image_path'] for sample in samples]
        results = processor.process_batch(image_paths, show_progress=True)
        
        # Calculate statistics
        statistics = processor.get_statistics(results)
        
        output = {
            'results': results,
            'statistics': statistics
        }
        
        # Compare with ground truth if requested
        if compare_ground_truth:
            accuracy = PipelineManager._calculate_accuracy(results, samples)
            output['accuracy'] = accuracy
            logger.info(f"Accuracy: {accuracy}")
        
        return output
    
    @staticmethod
    def _calculate_accuracy(results: List[Dict], samples: List[Dict]) -> Dict:
        """Calculate accuracy by comparing with ground truth."""
        field_accuracy = {
            'date': {'correct': 0, 'total': 0},
            'total': {'correct': 0, 'total': 0},
            'invoice_number': {'correct': 0, 'total': 0}
        }
        
        # Create lookup for ground truth
        gt_lookup = {sample['image_id']: sample for sample in samples}
        
        for result in results:
            if not result['metadata']['success']:
                continue
            
            image_id = result['image_id']
            if image_id not in gt_lookup:
                continue
            
            gt = gt_lookup[image_id]['entities']
            
            # Check each field
            for field_name in ['date', 'total', 'invoice_number']:
                if field_name not in gt:
                    continue
                
                field_accuracy[field_name]['total'] += 1
                
                pred_value = result['fields'][field_name]['value']
                true_value = gt[field_name]
                
                if PipelineManager._values_match(pred_value, true_value, field_name):
                    field_accuracy[field_name]['correct'] += 1
        
        # Calculate percentages
        accuracy = {}
        for field_name, counts in field_accuracy.items():
            if counts['total'] > 0:
                accuracy[field_name] = counts['correct'] / counts['total']
            else:
                accuracy[field_name] = 0.0
        
        # Overall accuracy
        total_correct = sum(counts['correct'] for counts in field_accuracy.values())
        total_count = sum(counts['total'] for counts in field_accuracy.values())
        accuracy['overall'] = total_correct / total_count if total_count > 0 else 0.0
        
        return accuracy
    
    @staticmethod
    def _values_match(pred_value: Any, true_value: Any, field_name: str) -> bool:
        """Check if predicted and true values match."""
        if pred_value is None or true_value is None:
            return False
        
        # Convert to strings for comparison
        pred_str = str(pred_value).strip().lower()
        true_str = str(true_value).strip().lower()
        
        if field_name == 'total':
            # For totals, allow small numerical differences
            try:
                pred_num = float(pred_str.replace('$', '').replace(',', ''))
                true_num = float(true_str.replace('$', '').replace(',', ''))
                return abs(pred_num - true_num) < 0.01
            except:
                return pred_str == true_str
        else:
            return pred_str == true_str
    
    @staticmethod
    def save_results(
        results: List[Dict],
        output_path: str,
        format: str = 'json'
    ):
        """
        Save processing results to file.
        
        Args:
            results: Processing results
            output_path: Output file path
            format: 'json' or 'csv'
        """
        output_path_obj = Path(output_path)
        ensure_path_exists(output_path_obj.parent)
        
        if format == 'json':
            PipelineManager._save_json(results, output_path_obj)
        elif format == 'csv':
            PipelineManager._save_csv(results, output_path_obj)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Results saved to {output_path_obj}")
    
    @staticmethod
    def _save_json(results: List[Dict], output_path: Path):
        """Save results as JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _save_csv(results: List[Dict], output_path: Path):
        """Save results as CSV."""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'image_id',
                'date_value', 'date_confidence',
                'total_value', 'total_confidence',
                'invoice_number_value', 'invoice_number_confidence',
                'processing_time', 'success'
            ])
            
            # Data
            for result in results:
                writer.writerow([
                    result['image_id'],
                    result['fields']['date']['value'],
                    f"{result['fields']['date']['confidence']:.4f}",
                    result['fields']['total']['value'],
                    f"{result['fields']['total']['confidence']:.4f}",
                    result['fields']['invoice_number']['value'],
                    f"{result['fields']['invoice_number']['confidence']:.4f}",
                    f"{result['metadata']['processing_time']:.4f}",
                    result['metadata']['success']
                ])


# Convenience function for quick processing
def process_image(image_path: str, **kwargs) -> Dict:
    """
    Quick convenience function to process a single image.
    
    Args:
        image_path: Path to image
        **kwargs: Additional arguments for DocumentProcessor
        
    Returns:
        Processing result
    """
    processor = DocumentProcessor(**kwargs)
    return processor.process_document(image_path)

# Made with Bob
