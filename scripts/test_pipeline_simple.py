#!/usr/bin/env python3
"""
Simple pipeline test without tqdm dependency.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.pipeline import DocumentProcessor

def main():
    """Test the pipeline with a single image."""
    
    # Get a sample image
    image_path = 'tests/SROIE2019/train/img/X00016469612.jpg'
    
    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        return 1
    
    print("="*80)
    print("TESTING PIPELINE")
    print("="*80)
    
    # Create processor
    print("\n1. Creating DocumentProcessor...")
    processor = DocumentProcessor(
        ocr_engine='tesseract',
        use_cache=True,
        use_calibration=False
    )
    print("   ✓ Processor created")
    
    # Process document
    print(f"\n2. Processing document: {image_path}")
    result = processor.process_document(image_path)
    
    # Display results
    print("\n3. Results:")
    print(f"   Success: {result['metadata']['success']}")
    print(f"   Processing Time: {result['metadata']['processing_time']:.3f}s")
    print(f"   OCR Engine: {result['metadata']['ocr_engine']}")
    print(f"   OCR Confidence: {result['metadata']['ocr_confidence']:.2%}")
    
    if result['metadata']['success']:
        print("\n4. Extracted Fields:")
        for field_name in ['date', 'total', 'invoice_number']:
            field = result['fields'][field_name]
            print(f"\n   {field_name.upper()}:")
            print(f"     Value:      {field['value']}")
            print(f"     Confidence: {field['confidence']:.2%}")
            print(f"     Raw Value:  {field['raw_value']}")
    else:
        print(f"\n   Error: {result['metadata'].get('error', 'Unknown')}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    return 0 if result['metadata']['success'] else 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
