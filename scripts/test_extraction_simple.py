#!/usr/bin/env python3
"""
Simple extraction test to validate core functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.extractor import ExtractionManager

def test_basic_extraction():
    """Test basic extraction with simple receipt text."""
    
    # Simulate OCR result
    ocr_result = {
        'text': """
        GROCERY STORE
        Receipt #12345
        Date: 30/03/2018
        
        Item 1: $5.00
        Item 2: $3.50
        
        Subtotal: $8.50
        Tax: $1.50
        Total: $10.00
        
        Thank you!
        """,
        'confidence': 0.95,
        'metadata': {}
    }
    
    # Extract fields
    manager = ExtractionManager()
    result = manager.extract_fields(ocr_result)
    
    # Print results
    print("="*80)
    print("EXTRACTION TEST RESULTS")
    print("="*80)
    
    print(f"\nDate:")
    print(f"  Value:      {result['date']['value']}")
    print(f"  Confidence: {result['date']['confidence']:.2%}")
    print(f"  Expected:   2018-03-30")
    print(f"  Match:      {'✓' if result['date']['value'] == '2018-03-30' else '✗'}")
    
    print(f"\nTotal:")
    print(f"  Value:      ${result['total']['value']:.2f}" if result['total']['value'] else "  Value:      None")
    print(f"  Confidence: {result['total']['confidence']:.2%}")
    print(f"  Expected:   $10.00")
    print(f"  Match:      {'✓' if result['total']['value'] == 10.00 else '✗'}")
    
    print(f"\nInvoice Number:")
    print(f"  Value:      {result['invoice_number']['value']}")
    print(f"  Confidence: {result['invoice_number']['confidence']:.2%}")
    print(f"  Expected:   12345 (or similar)")
    
    print(f"\nMetadata:")
    print(f"  Extraction Time: {result['metadata']['extraction_time']:.3f}s")
    print(f"  Candidates:")
    for field, count in result['metadata']['candidates_considered'].items():
        print(f"    {field}: {count}")
    
    # Summary
    print("\n" + "="*80)
    date_ok = result['date']['value'] == '2018-03-30'
    total_ok = result['total']['value'] == 10.00
    
    if date_ok and total_ok:
        print("✓ BASIC EXTRACTION TEST PASSED")
    else:
        print("✗ BASIC EXTRACTION TEST FAILED")
        if not date_ok:
            print(f"  - Date mismatch: got {result['date']['value']}")
        if not total_ok:
            print(f"  - Total mismatch: got {result['total']['value']}")
    print("="*80)
    
    return date_ok and total_ok


if __name__ == '__main__':
    success = test_basic_extraction()
    sys.exit(0 if success else 1)

# Made with Bob
