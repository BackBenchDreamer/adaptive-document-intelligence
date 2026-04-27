"""
Basic usage example for Adaptive Document Intelligence System.

This example demonstrates how to process a single document
and extract structured fields.
"""

from pipeline.pipeline import DocumentProcessor

def main():
    """Process a single document and print results."""
    # Initialize processor with Tesseract OCR
    processor = DocumentProcessor(ocr_engine='tesseract')
    
    # Process document
    print("Processing document...")
    result = processor.process_document('path/to/receipt.jpg')
    
    # Check if processing was successful
    if result['metadata']['success']:
        # Extract fields
        date = result['fields']['date']
        total = result['fields']['total']
        invoice = result['fields']['invoice_number']
        
        # Print results
        print("\n=== Extraction Results ===")
        print(f"Date: {date['value']} (confidence: {date['confidence']:.2f})")
        print(f"Total: ${total['value']:.2f} (confidence: {total['confidence']:.2f})")
        print(f"Invoice: {invoice['value']} (confidence: {invoice['confidence']:.2f})")
        
        # Print metadata
        print(f"\nProcessing time: {result['metadata']['processing_time']:.2f}s")
        print(f"OCR engine: {result['metadata']['ocr_engine']}")
    else:
        print(f"Processing failed: {result['metadata']['error']}")

if __name__ == '__main__':
    main()
