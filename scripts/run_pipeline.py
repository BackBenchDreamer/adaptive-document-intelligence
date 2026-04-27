#!/usr/bin/env python3
"""
Pipeline CLI Script

Command-line interface for running the document processing pipeline.

Usage:
    # Single image
    python scripts/run_pipeline.py --image receipt.jpg
    
    # Batch processing
    python scripts/run_pipeline.py --batch images/ --output results.json
    
    # SROIE dataset
    python scripts/run_pipeline.py --sroie train --limit 100 --compare-gt
    
    # With options
    python scripts/run_pipeline.py --batch images/ --no-cache --no-preprocessing

Author: Adaptive Document Intelligence System
Phase: 6 - Pipeline Integration
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.pipeline import (
    DocumentProcessor,
    BatchProcessor,
    PipelineManager
)
from core.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def process_single_image(args):
    """Process a single image."""
    logger.info(f"Processing single image: {args.image}")
    
    # Create processor
    processor = DocumentProcessor(
        ocr_engine=args.engine,
        use_preprocessing=not args.no_preprocessing,
        use_cache=not args.no_cache,
        use_calibration=args.calibration
    )
    
    # Process image
    result = processor.process_document(
        args.image,
        return_intermediate=args.verbose
    )
    
    # Print results
    print("\n" + "="*80)
    print("PROCESSING RESULT")
    print("="*80)
    
    print(f"\nImage: {result['image_id']}")
    print(f"Success: {result['metadata']['success']}")
    print(f"Processing Time: {result['metadata']['processing_time']:.3f}s")
    print(f"OCR Engine: {result['metadata']['ocr_engine']}")
    print(f"OCR Confidence: {result['metadata']['ocr_confidence']:.2%}")
    
    if result['metadata']['success']:
        print("\nExtracted Fields:")
        print("-" * 80)
        
        for field_name in ['date', 'total', 'invoice_number']:
            field = result['fields'][field_name]
            print(f"\n{field_name.upper()}:")
            print(f"  Value:      {field['value']}")
            print(f"  Confidence: {field['confidence']:.2%}")
            print(f"  Raw Value:  {field['raw_value']}")
    else:
        print(f"\nError: {result['metadata'].get('error', 'Unknown error')}")
    
    # Save if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nResult saved to: {output_path}")
    
    print("\n" + "="*80)
    
    return 0 if result['metadata']['success'] else 1


def process_batch(args):
    """Process a batch of images."""
    logger.info(f"Processing batch from: {args.batch}")
    
    # Create processor
    processor = DocumentProcessor(
        ocr_engine=args.engine,
        use_preprocessing=not args.no_preprocessing,
        use_cache=not args.no_cache,
        use_calibration=args.calibration
    )
    
    # Create batch processor
    batch_processor = BatchProcessor(
        processor,
        max_workers=args.workers,
        use_parallel=args.parallel
    )
    
    # Process directory
    result = batch_processor.process_directory(
        args.batch,
        pattern=args.pattern,
        limit=args.limit
    )
    
    # Print statistics
    print("\n" + "="*80)
    print("BATCH PROCESSING RESULTS")
    print("="*80)
    
    stats = result['statistics']
    print(f"\nTotal Processed: {stats['total_processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Average Processing Time: {stats['avg_processing_time']:.3f}s")
    
    print("\nAverage Confidence:")
    for field, conf in stats['avg_confidence'].items():
        print(f"  {field}: {conf:.2%}")
    
    print("\nExtraction Rate:")
    for field, rate in stats['extraction_rate'].items():
        print(f"  {field}: {rate:.2%}")
    
    # Print errors if any
    if result['errors']:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result['errors'][:5]:  # Show first 5
            print(f"  - {error['image_id']}: {error['error']}")
        if len(result['errors']) > 5:
            print(f"  ... and {len(result['errors']) - 5} more")
    
    # Save results if output specified
    if args.output:
        format_type = 'csv' if args.output.endswith('.csv') else 'json'
        PipelineManager.save_results(
            result['results'],
            args.output,
            format=format_type
        )
        print(f"\nResults saved to: {args.output}")
    
    print("\n" + "="*80)
    
    return 0 if stats['failed'] == 0 else 1


def process_sroie(args):
    """Process SROIE dataset."""
    logger.info(f"Processing SROIE {args.sroie} dataset")
    
    # Create config
    config = {
        'ocr_engine': args.engine,
        'use_preprocessing': not args.no_preprocessing,
        'use_cache': not args.no_cache,
        'use_calibration': args.calibration
    }
    
    # Process dataset
    result = PipelineManager.process_sroie_dataset(
        split=args.sroie,
        limit=args.limit,
        compare_ground_truth=args.compare_gt,
        config=config
    )
    
    # Print statistics
    print("\n" + "="*80)
    print(f"SROIE {args.sroie.upper()} DATASET RESULTS")
    print("="*80)
    
    stats = result['statistics']
    print(f"\nTotal Processed: {stats['total_processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Average Processing Time: {stats['avg_processing_time']:.3f}s")
    
    print("\nAverage Confidence:")
    for field, conf in stats['avg_confidence'].items():
        print(f"  {field}: {conf:.2%}")
    
    print("\nExtraction Rate:")
    for field, rate in stats['extraction_rate'].items():
        print(f"  {field}: {rate:.2%}")
    
    # Print accuracy if available
    if 'accuracy' in result:
        print("\nAccuracy (vs Ground Truth):")
        for field, acc in result['accuracy'].items():
            print(f"  {field}: {acc:.2%}")
    
    # Save results if output specified
    if args.output:
        format_type = 'csv' if args.output.endswith('.csv') else 'json'
        PipelineManager.save_results(
            result['results'],
            args.output,
            format=format_type
        )
        print(f"\nResults saved to: {args.output}")
    
    print("\n" + "="*80)
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Document Processing Pipeline CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single image
  python scripts/run_pipeline.py --image receipt.jpg
  
  # Process batch with output
  python scripts/run_pipeline.py --batch images/ --output results.json
  
  # Process SROIE dataset
  python scripts/run_pipeline.py --sroie train --limit 100 --compare-gt
  
  # Use PaddleOCR instead of Tesseract
  python scripts/run_pipeline.py --image receipt.jpg --engine paddleocr
  
  # Parallel batch processing
  python scripts/run_pipeline.py --batch images/ --parallel --workers 4
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--image',
        type=str,
        help='Process a single image'
    )
    input_group.add_argument(
        '--batch',
        type=str,
        help='Process a batch of images from directory'
    )
    input_group.add_argument(
        '--sroie',
        type=str,
        choices=['train', 'test'],
        help='Process SROIE dataset (train or test)'
    )
    
    # Processing options
    parser.add_argument(
        '--engine',
        type=str,
        choices=['tesseract', 'paddleocr'],
        default='tesseract',
        help='OCR engine to use (default: tesseract)'
    )
    parser.add_argument(
        '--no-preprocessing',
        action='store_true',
        help='Disable image preprocessing'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable OCR result caching'
    )
    parser.add_argument(
        '--calibration',
        action='store_true',
        help='Enable confidence calibration'
    )
    
    # Batch options
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.jpg',
        help='File pattern for batch processing (default: *.jpg)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of images to process'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Enable parallel processing for batch'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    
    # SROIE options
    parser.add_argument(
        '--compare-gt',
        action='store_true',
        help='Compare with ground truth (SROIE only)'
    )
    
    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (.json or .csv)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Include intermediate results in output'
    )
    
    args = parser.parse_args()
    
    # Route to appropriate handler
    try:
        if args.image:
            return process_single_image(args)
        elif args.batch:
            return process_batch(args)
        elif args.sroie:
            return process_sroie(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nError: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
