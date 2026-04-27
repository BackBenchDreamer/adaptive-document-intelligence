#!/usr/bin/env python3
"""
Simple confidence scoring test without OCR dependencies.

Tests the confidence scoring module in isolation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.confidence import (
    MultiFactorConfidenceScorer,
    ConfidenceCalibrator,
    ConfidenceManager
)


def test_confidence_factors():
    """Test individual confidence factor calculations."""
    
    print("\n" + "="*80)
    print("CONFIDENCE FACTOR TESTS")
    print("="*80)
    
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
        status = "✓" if score >= 0.7 else "✗"
        print(f"   {status} {description:<25} '{date_str}' → {score:.2f}")
    
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
        status = "✓" if score >= 0.5 else "✗"
        print(f"   {status} {description:<25} ${amount} → {score:.2f}")
    
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
        status = "✓" if score >= 0.5 else "✗"
        print(f"   {status} {description:<25} '{invoice}' → {score:.2f}")
    
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
        status = "✓" if score >= 0.8 else "⚠"
        print(f"     {status} {description:<20} '{pattern}' → {score:.2f}")
    
    print("\n   Total Patterns:")
    total_patterns = [
        ('$4.95', 'Currency symbol'),
        ('4.95', 'Plain decimal'),
        ('$1,234.56', 'With comma'),
    ]
    for pattern, description in total_patterns:
        score = scorer._check_total_pattern(pattern)
        status = "✓" if score >= 0.8 else "⚠"
        print(f"     {status} {description:<20} '{pattern}' → {score:.2f}")
    
    print("\n   Invoice Patterns:")
    invoice_patterns = [
        ('INV-12345', 'INV prefix'),
        ('#12345', 'Hash prefix'),
        ('ABC-123', 'Letter-number'),
    ]
    for pattern, description in invoice_patterns:
        score = scorer._check_invoice_pattern(pattern)
        status = "✓" if score >= 0.8 else "⚠"
        print(f"     {status} {description:<20} '{pattern}' → {score:.2f}")
    
    print("\n" + "="*80)


def test_multi_factor_scoring():
    """Test multi-factor confidence scoring."""
    
    print("\n" + "="*80)
    print("MULTI-FACTOR SCORING TEST")
    print("="*80)
    
    scorer = MultiFactorConfidenceScorer()
    
    # Test case 1: High quality extraction
    print("\n1. High Quality Extraction:")
    extraction_result = {
        'value': '2018-03-30',
        'confidence': 0.95,
        'raw_value': '30/03/2018'
    }
    ocr_result = {
        'text': 'Receipt with date 30/03/2018 and other text',
        'confidence': 0.90
    }
    
    confidence, factors = scorer.calculate_confidence(
        extraction_result,
        ocr_result,
        'date'
    )
    
    print(f"   Final Confidence: {confidence:.3f}")
    print(f"   Factors:")
    for factor, value in factors.items():
        print(f"     - {factor}: {value:.3f}")
    
    # Test case 2: Medium quality extraction
    print("\n2. Medium Quality Extraction:")
    extraction_result = {
        'value': 4.95,
        'confidence': 0.70,
        'raw_value': '4.95'
    }
    ocr_result = {
        'text': 'Short text',
        'confidence': 0.60
    }
    
    confidence, factors = scorer.calculate_confidence(
        extraction_result,
        ocr_result,
        'total'
    )
    
    print(f"   Final Confidence: {confidence:.3f}")
    print(f"   Factors:")
    for factor, value in factors.items():
        print(f"     - {factor}: {value:.3f}")
    
    # Test case 3: Low quality extraction
    print("\n3. Low Quality Extraction:")
    extraction_result = {
        'value': None,
        'confidence': 0.30,
        'raw_value': ''
    }
    ocr_result = {
        'text': '',
        'confidence': 0.40
    }
    
    confidence, factors = scorer.calculate_confidence(
        extraction_result,
        ocr_result,
        'invoice_number'
    )
    
    print(f"   Final Confidence: {confidence:.3f}")
    print(f"   Factors:")
    for factor, value in factors.items():
        print(f"     - {factor}: {value:.3f}")
    
    print("\n" + "="*80)


def test_confidence_manager():
    """Test confidence manager."""
    
    print("\n" + "="*80)
    print("CONFIDENCE MANAGER TEST")
    print("="*80)
    
    manager = ConfidenceManager(use_calibration=False)
    
    # Mock extraction results
    extraction_results = {
        'date': {
            'value': '2018-03-30',
            'confidence': 0.90,
            'raw_value': '30/03/2018'
        },
        'total': {
            'value': 4.95,
            'confidence': 0.85,
            'raw_value': '$4.95'
        },
        'invoice_number': {
            'value': 'INV-12345',
            'confidence': 0.80,
            'raw_value': 'INV-12345'
        }
    }
    
    ocr_result = {
        'text': 'Receipt with date 30/03/2018, total $4.95, invoice INV-12345',
        'confidence': 0.88
    }
    
    print("\nScoring extraction results...")
    scored_results = manager.score_extraction(extraction_results, ocr_result)
    
    print("\nResults:")
    print(f"{'─'*80}")
    print(f"{'Field':<15} {'Value':<25} {'Confidence':<12} {'Raw Conf':<10}")
    print(f"{'─'*80}")
    
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
            
            print(f"{status} {field_name:<13} {value:<25} {conf:<12.3f} {raw_conf:<10.3f}")
            
            # Show factor breakdown
            factors = field_data['confidence_factors']
            print(f"  Factors: ext={factors['extraction']:.2f}, "
                  f"ocr={factors['ocr_quality']:.2f}, "
                  f"val={factors['validity']:.2f}, "
                  f"pat={factors['pattern']:.2f}")
    
    print(f"{'─'*80}")
    
    # Metadata
    metadata = scored_results['metadata']
    print(f"\nMetadata:")
    print(f"  - Calibration applied: {metadata['calibration_applied']}")
    print(f"  - Scoring time: {metadata['scoring_time']*1000:.2f}ms")
    
    print("\n" + "="*80)


def test_calibrator():
    """Test confidence calibrator."""
    
    print("\n" + "="*80)
    print("CALIBRATOR TEST")
    print("="*80)
    
    calibrator = ConfidenceCalibrator()
    
    print("\n1. Default Bins:")
    for field_name in ['date', 'total', 'invoice_number']:
        bins = calibrator._get_default_bins(field_name)
        print(f"\n   {field_name}:")
        for threshold, calibrated in bins:
            print(f"     {threshold:.1f} → {calibrated:.2f}")
    
    print("\n2. Calibration Test:")
    test_scores = [0.5, 0.7, 0.85, 0.95]
    
    for field_name in ['date', 'total']:
        print(f"\n   {field_name}:")
        for score in test_scores:
            calibrated = calibrator.calibrate(score, field_name)
            print(f"     Raw {score:.2f} → Calibrated {calibrated:.2f}")
    
    print("\n" + "="*80)


def main():
    """Main entry point."""
    
    print("\n" + "="*80)
    print("CONFIDENCE SCORING MODULE TEST")
    print("="*80)
    
    try:
        # Run all tests
        test_confidence_factors()
        test_multi_factor_scoring()
        test_confidence_manager()
        test_calibrator()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80 + "\n")
        
        return 0
    
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
