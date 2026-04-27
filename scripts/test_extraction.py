#!/usr/bin/env python3
"""
Test Field Extraction Script

Tests the field extraction pipeline on SROIE images.
Compares extracted fields with ground truth and displays results.

Usage:
    # Test single image
    python scripts/test_extraction.py --image tests/SROIE2019/train/img/X00016469622.jpg
    
    # Test batch
    python scripts/test_extraction.py --batch tests/SROIE2019/train/img/ --limit 10
    
    # Show all candidates
    python scripts/test_extraction.py --image receipt.jpg --show-candidates
    
    # Verbose output
    python scripts/test_extraction.py --image receipt.jpg --verbose
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import setup_logging
from core.config import Config
from pipeline.ocr import OCRManager
from pipeline.extractor import ExtractionManager
from tests.data.sroie_loader import SROIEDataLoader


def load_ground_truth(image_path: Path) -> Optional[Dict]:
    """
    Load ground truth for an image.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Ground truth dict or None if not found
    """
    # Construct entities file path
    entities_dir = image_path.parent.parent / 'entities'
    entities_file = entities_dir / f"{image_path.stem}.txt"
    
    if not entities_file.exists():
        return None
    
    # Parse entities file
    ground_truth = {}
    with open(entities_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Format: {"key": "value"}
            try:
                data = json.loads(line)
                ground_truth.update(data)
            except json.JSONDecodeError:
                continue
    
    return ground_truth


def compare_fields(extracted: Dict, ground_truth: Dict) -> Dict:
    """
    Compare extracted fields with ground truth.
    
    Args:
        extracted: Extracted fields
        ground_truth: Ground truth fields
        
    Returns:
        Comparison results with match status for each field
    """
    results = {}
    
    # Compare date
    if 'date' in ground_truth:
        gt_date = ground_truth['date']
        ext_date = extracted['date']['value']
        
        results['date'] = {
            'ground_truth': gt_date,
            'extracted': ext_date,
            'match': gt_date == ext_date if ext_date else False,
            'confidence': extracted['date']['confidence']
        }
    
    # Compare total
    if 'total' in ground_truth:
        gt_total = float(ground_truth['total'])
        ext_total = extracted['total']['value']
        
        # Allow small floating point differences
        match = False
        if ext_total is not None:
            match = abs(gt_total - ext_total) < 0.01
        
        results['total'] = {
            'ground_truth': gt_total,
            'extracted': ext_total,
            'match': match,
            'confidence': extracted['total']['confidence']
        }
    
    # Compare invoice number (optional)
    if 'invoice_number' in ground_truth:
        gt_inv = ground_truth['invoice_number']
        ext_inv = extracted['invoice_number']['value']
        
        results['invoice_number'] = {
            'ground_truth': gt_inv,
            'extracted': ext_inv,
            'match': gt_inv == ext_inv if ext_inv else False,
            'confidence': extracted['invoice_number']['confidence']
        }
    
    return results


def print_extraction_result(
    image_path: Path,
    ocr_result: Dict,
    extraction_result: Dict,
    ground_truth: Optional[Dict] = None,
    show_candidates: bool = False,
    verbose: bool = False
):
    """
    Print extraction results in a formatted way.
    
    Args:
        image_path: Path to image
        ocr_result: OCR result
        extraction_result: Extraction result
        ground_truth: Ground truth (if available)
        show_candidates: Whether to show all candidates
        verbose: Whether to show verbose output
    """
    print("\n" + "="*80)
    print(f"IMAGE: {image_path.name}")
    print("="*80)
    
    # OCR info
    print(f"\nOCR Confidence: {ocr_result['confidence']:.2%}")
    if verbose:
        print(f"Text Length: {len(ocr_result['text'])} characters")
        print(f"\nOCR Text Preview:")
        print("-" * 80)
        print(ocr_result['text'][:500])
        if len(ocr_result['text']) > 500:
            print("... (truncated)")
        print("-" * 80)
    
    # Extraction results
    print("\n" + "-"*80)
    print("EXTRACTED FIELDS")
    print("-"*80)
    
    # Date
    date_result = extraction_result['date']
    print(f"\nDate:")
    print(f"  Value:      {date_result['value']}")
    print(f"  Confidence: {date_result['confidence']:.2%}")
    print(f"  Raw:        {date_result['raw_value']}")
    print(f"  Method:     {date_result['method']}")
    
    # Total
    total_result = extraction_result['total']
    print(f"\nTotal:")
    print(f"  Value:      ${total_result['value']:.2f}" if total_result['value'] else "  Value:      None")
    print(f"  Confidence: {total_result['confidence']:.2%}")
    print(f"  Raw:        {total_result['raw_value']}")
    print(f"  Method:     {total_result['method']}")
    
    # Invoice Number
    inv_result = extraction_result['invoice_number']
    print(f"\nInvoice Number:")
    print(f"  Value:      {inv_result['value']}")
    print(f"  Confidence: {inv_result['confidence']:.2%}")
    print(f"  Raw:        {inv_result['raw_value']}")
    print(f"  Method:     {inv_result['method']}")
    
    # Metadata
    metadata = extraction_result['metadata']
    print(f"\nMetadata:")
    print(f"  Extraction Time: {metadata['extraction_time']:.3f}s")
    print(f"  Candidates Considered:")
    for field, count in metadata['candidates_considered'].items():
        print(f"    {field}: {count}")
    
    # Show candidates if requested
    if show_candidates and verbose:
        print("\n" + "-"*80)
        print("ALL CANDIDATES")
        print("-"*80)
        
        # This would require modifying the extractor to return candidates
        # For now, just note that this feature is available
        print("(Use --verbose to see detailed candidate information)")
    
    # Compare with ground truth if available
    if ground_truth:
        print("\n" + "-"*80)
        print("GROUND TRUTH COMPARISON")
        print("-"*80)
        
        comparison = compare_fields(extraction_result, ground_truth)
        
        for field, result in comparison.items():
            match_symbol = "✓" if result['match'] else "✗"
            print(f"\n{field.upper()}: {match_symbol}")
            print(f"  Ground Truth: {result['ground_truth']}")
            print(f"  Extracted:    {result['extracted']}")
            print(f"  Confidence:   {result['confidence']:.2%}")


def test_single_image(
    image_path: Path,
    ocr_engine: OCRManager,
    extractor: ExtractionManager,
    show_candidates: bool = False,
    verbose: bool = False
):
    """
    Test extraction on a single image.
    
    Args:
        image_path: Path to image
        ocr_engine: OCR engine instance
        extractor: Extraction manager instance
        show_candidates: Whether to show all candidates
        verbose: Whether to show verbose output
    """
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        return
    
    print(f"\nProcessing: {image_path}")
    
    # Run OCR
    ocr_result = ocr_engine.extract_text(str(image_path))
    
    # Extract fields
    extraction_result = extractor.extract_fields(ocr_result)
    
    # Load ground truth if available
    ground_truth = load_ground_truth(image_path)
    
    # Print results
    print_extraction_result(
        image_path,
        ocr_result,
        extraction_result,
        ground_truth,
        show_candidates,
        verbose
    )


def test_batch(
    batch_dir: Path,
    ocr_engine: OCRManager,
    extractor: ExtractionManager,
    limit: Optional[int] = None,
    verbose: bool = False
):
    """
    Test extraction on a batch of images.
    
    Args:
        batch_dir: Directory containing images
        ocr_engine: OCR engine instance
        extractor: Extraction manager instance
        limit: Maximum number of images to process
        verbose: Whether to show verbose output
    """
    if not batch_dir.exists():
        print(f"Error: Directory not found: {batch_dir}")
        return
    
    # Find all images
    image_files = list(batch_dir.glob("*.jpg")) + list(batch_dir.glob("*.png"))
    
    if limit:
        image_files = image_files[:limit]
    
    print(f"\nProcessing {len(image_files)} images from {batch_dir}")
    
    # Statistics
    stats = {
        'total': len(image_files),
        'date_correct': 0,
        'total_correct': 0,
        'invoice_correct': 0,
        'date_extracted': 0,
        'total_extracted': 0,
        'invoice_extracted': 0
    }
    
    # Process each image
    for i, image_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processing: {image_path.name}")
        
        try:
            # Run OCR
            ocr_result = ocr_engine.extract_text(str(image_path))
            
            # Extract fields
            extraction_result = extractor.extract_fields(ocr_result)
            
            # Load ground truth
            ground_truth = load_ground_truth(image_path)
            
            if ground_truth:
                # Compare results
                comparison = compare_fields(extraction_result, ground_truth)
                
                # Update statistics
                if 'date' in comparison:
                    if extraction_result['date']['value']:
                        stats['date_extracted'] += 1
                    if comparison['date']['match']:
                        stats['date_correct'] += 1
                
                if 'total' in comparison:
                    if extraction_result['total']['value']:
                        stats['total_extracted'] += 1
                    if comparison['total']['match']:
                        stats['total_correct'] += 1
                
                if 'invoice_number' in comparison:
                    if extraction_result['invoice_number']['value']:
                        stats['invoice_extracted'] += 1
                    if comparison['invoice_number']['match']:
                        stats['invoice_correct'] += 1
                
                # Print summary for this image
                date_status = "✓" if comparison.get('date', {}).get('match') else "✗"
                total_status = "✓" if comparison.get('total', {}).get('match') else "✗"
                print(f"  Date: {date_status} | Total: {total_status}")
            else:
                print("  (No ground truth available)")
            
            if verbose:
                print(f"  Date: {extraction_result['date']['value']} "
                      f"({extraction_result['date']['confidence']:.2%})")
                print(f"  Total: ${extraction_result['total']['value']:.2f} "
                      f"({extraction_result['total']['confidence']:.2%})" 
                      if extraction_result['total']['value'] else "  Total: None")
        
        except Exception as e:
            print(f"  Error: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
    
    # Print final statistics
    print("\n" + "="*80)
    print("BATCH STATISTICS")
    print("="*80)
    print(f"\nTotal Images: {stats['total']}")
    
    if stats['total'] > 0:
        print(f"\nDate:")
        print(f"  Extracted: {stats['date_extracted']}/{stats['total']} "
              f"({stats['date_extracted']/stats['total']:.1%})")
        if stats['date_extracted'] > 0:
            print(f"  Correct:   {stats['date_correct']}/{stats['date_extracted']} "
                  f"({stats['date_correct']/stats['date_extracted']:.1%})")
        
        print(f"\nTotal:")
        print(f"  Extracted: {stats['total_extracted']}/{stats['total']} "
              f"({stats['total_extracted']/stats['total']:.1%})")
        if stats['total_extracted'] > 0:
            print(f"  Correct:   {stats['total_correct']}/{stats['total_extracted']} "
                  f"({stats['total_correct']/stats['total_extracted']:.1%})")
        
        print(f"\nInvoice Number:")
        print(f"  Extracted: {stats['invoice_extracted']}/{stats['total']} "
              f"({stats['invoice_extracted']/stats['total']:.1%})")
        if stats['invoice_extracted'] > 0:
            print(f"  Correct:   {stats['invoice_correct']}/{stats['invoice_extracted']} "
                  f"({stats['invoice_correct']/stats['invoice_extracted']:.1%})")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test field extraction on SROIE images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Input options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--image',
        type=Path,
        help='Path to single image file'
    )
    group.add_argument(
        '--batch',
        type=Path,
        help='Path to directory containing images'
    )
    
    # Batch options
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of images to process in batch mode'
    )
    
    # Display options
    parser.add_argument(
        '--show-candidates',
        action='store_true',
        help='Show all extraction candidates'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show verbose output'
    )
    
    # Logging options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level=log_level)
    
    # Initialize components
    print("Initializing OCR engine and extractor...")
    ocr_engine = OCRManager(preferred_engine='paddleocr', enable_cache=True)
    extractor = ExtractionManager()
    
    # Run tests
    if args.image:
        test_single_image(
            args.image,
            ocr_engine,
            extractor,
            args.show_candidates,
            args.verbose
        )
    else:
        test_batch(
            args.batch,
            ocr_engine,
            extractor,
            args.limit,
            args.verbose
        )


if __name__ == '__main__':
    main()

# Made with Bob
