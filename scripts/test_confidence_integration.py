#!/usr/bin/env python3
"""
Test confidence scoring integration with extraction pipeline.

This script demonstrates the complete flow:
1. Load a sample image
2. Run OCR
3. Extract fields
4. Score confidence
5. Display results
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.ocr import OCRManager
from pipeline.extractor import ExtractionManager
from pipeline.confidence import ConfidenceManager
from core.logging_config import get_logger

logger = get_logger(__name__)


def test_confidence_integration():
    """Test complete pipeline with confidence scoring."""
    
    print("="*80)
    print("CONFIDENCE SCORING INTEGRATION TEST")
    print("="*80)
    
    # Find a test image
    test_image_dir = project_root / 'tests' / 'SROIE2019' / 'train' / 'img'
    test_images = list(test_image_dir.glob('*.jpg'))[:3]  # Test first 3 images
    
    if not test_images:
        print("❌ No test images found!")
        return False
    
    print(f"\nTesting with {len(test_images)} images...\n")
    
    # Initialize pipeline components
    print("Initializing components...")
    ocr_engine = OCRManager(preferred_engine='paddleocr')
    extractor = ExtractionManager()
    confidence_mgr = ConfidenceManager(use_calibration=False)
    print("✓ Components initialized\n")
    
    # Process each image
    for i, image_path in enumerate(test_images, 1):
        print(f"\n{'='*80}")
        print(f"Image {i}/{len(test_images)}: {image_path.name}")
        print(f"{'='*80}")
        
        try:
            # Step 1: OCR
            print("\n1. Running OCR...")
            ocr_result = ocr_engine.extract_text(str(image_path))
            print(f"   ✓ Extracted {len(ocr_result['text'])} characters")
            print(f"   ✓ OCR confidence: {ocr_result['confidence']:.3f}")
            print(f"   ✓ Engine: {ocr_result['engine']}")
            
            # Step 2: Extract fields
            print("\n2. Extracting fields...")
            extraction_results = extractor.extract_fields(ocr_result)
            
            extracted_fields = [f for f in ['date', 'total', 'invoice_number'] 
                              if f in extraction_results]
            print(f"   ✓ Extracted {len(extracted_fields)} fields: {', '.join(extracted_fields)}")
            
            # Step 3: Score confidence
            print("\n3. Scoring confidence...")
            scored_results = confidence_mgr.score_extraction(
                extraction_results,
                ocr_result
            )
            
            # Display results
            print("\n4. Results:")
            print(f"   {'─'*76}")
            print(f"   {'Field':<15} {'Value':<25} {'Confidence':<12} {'Raw Conf':<10}")
            print(f"   {'─'*76}")
            
            for field_name in ['date', 'total', 'invoice_number']:
                if field_name in scored_results:
                    field_data = scored_results[field_name]
                    value = str(field_data['value'])[:23]
                    conf = field_data['confidence']
                    raw_conf = field_data['raw_confidence']
                    
                    # Color code by confidence
                    if conf >= 0.80:
                        status = "✓"
                    elif conf >= 0.60:
                        status = "⚠"
                    else:
                        status = "✗"
                    
                    print(f"   {status} {field_name:<13} {value:<25} {conf:<12.3f} {raw_conf:<10.3f}")
                    
                    # Show factor breakdown
                    factors = field_data['confidence_factors']
                    print(f"     Factors: ext={factors['extraction']:.2f}, "
                          f"ocr={factors['ocr_quality']:.2f}, "
                          f"val={factors['validity']:.2f}, "
                          f"pat={factors['pattern']:.2f}")
            
            print(f"   {'─'*76}")
            
            # Metadata
            metadata = scored_results['metadata']
            print(f"\n   Metadata:")
            print(f"   - Calibration applied: {metadata['calibration_applied']}")
            print(f"   - Scoring time: {metadata['scoring_time']*1000:.2f}ms")
            
            print(f"\n   ✓ Successfully processed {image_path.name}")
            
        except Exception as e:
            print(f"\n   ✗ Error processing {image_path.name}: {e}")
            logger.error(f"Error processing {image_path.name}", exc_info=True)
            continue
    
    print(f"\n{'='*80}")
    print("INTEGRATION TEST COMPLETE")
    print(f"{'='*80}\n")
    
    return True


def test_confidence_factors():
    """Test individual confidence factor calculations."""
    
    print("\n" + "="*80)
    print("CONFIDENCE FACTOR TESTS")
    print("="*80)
    
    from pipeline.confidence import MultiFactorConfidenceScorer
    
    scorer = MultiFactorConfidenceScorer()
    
    # Test date validation
    print("\n1. Date Validation:")
    test_dates = [
        ('2018-03-30', 'Valid recent date'),
        ('2000-01-01', 'Valid old date'),
        ('1800-01-01', 'Invalid year'),
        ('2030-01-01', 'Future date'),
    ]
    
    for date_str, description in test_dates:
        score = scorer._validate_date(date_str)
        print(f"   {description:<25} '{date_str}' → {score:.2f}")
    
    # Test total validation
    print("\n2. Total Validation:")
    test_totals = [
        (4.95, 'Normal amount'),
        (1000.0, 'Round number'),
        (-10.0, 'Negative'),
        (200000.0, 'Too large'),
    ]
    
    for amount, description in test_totals:
        score = scorer._validate_total(amount)
        print(f"   {description:<25} ${amount} → {score:.2f}")
    
    # Test invoice validation
    print("\n3. Invoice Number Validation:")
    test_invoices = [
        ('INV-12345', 'Standard format'),
        ('ABC123XYZ', 'Alphanumeric'),
        ('AB', 'Too short'),
        ('---', 'No alphanumeric'),
    ]
    
    for invoice, description in test_invoices:
        score = scorer._validate_invoice_number(invoice)
        print(f"   {description:<25} '{invoice}' → {score:.2f}")
    
    # Test pattern matching
    print("\n4. Pattern Matching:")
    
    print("\n   Date Patterns:")
    date_patterns = [
        ('30/03/2018', 'DD/MM/YYYY'),
        ('2018-03-30', 'ISO format'),
        ('March 30, 2018', 'Text format'),
    ]
    for pattern, description in date_patterns:
        score = scorer._check_date_pattern(pattern)
        print(f"     {description:<20} '{pattern}' → {score:.2f}")
    
    print("\n   Total Patterns:")
    total_patterns = [
        ('$4.95', 'Currency symbol'),
        ('4.95', 'Plain decimal'),
        ('$1,234.56', 'With comma'),
    ]
    for pattern, description in total_patterns:
        score = scorer._check_total_pattern(pattern)
        print(f"     {description:<20} '{pattern}' → {score:.2f}")
    
    print("\n   Invoice Patterns:")
    invoice_patterns = [
        ('INV-12345', 'INV prefix'),
        ('#12345', 'Hash prefix'),
        ('ABC-123', 'Letter-number'),
    ]
    for pattern, description in invoice_patterns:
        score = scorer._check_invoice_pattern(pattern)
        print(f"     {description:<20} '{pattern}' → {score:.2f}")
    
    print("\n" + "="*80)
    print("FACTOR TESTS COMPLETE")
    print("="*80 + "\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test confidence scoring integration'
    )
    parser.add_argument(
        '--factors-only',
        action='store_true',
        help='Only test confidence factors'
    )
    
    args = parser.parse_args()
    
    try:
        if args.factors_only:
            test_confidence_factors()
        else:
            # Run both tests
            success = test_confidence_integration()
            test_confidence_factors()
            
            if success:
                print("\n✓ All integration tests passed!")
                return 0
            else:
                print("\n✗ Some tests failed")
                return 1
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.error("Test failed", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
