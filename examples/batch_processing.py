"""
Batch processing example.

This example demonstrates how to process multiple documents
in a directory and save results to a file.
"""

from pipeline import BatchProcessor, DocumentProcessor
from pathlib import Path
import json

def main():
    """Process a batch of documents."""
    # Initialize processor
    processor = DocumentProcessor(ocr_engine='tesseract')
    
    # Initialize batch processor with parallel processing
    batch = BatchProcessor(
        processor,
        max_workers=4,
        use_parallel=True
    )
    
    # Process directory
    print("Processing batch...")
    results = batch.process_directory(
        directory='path/to/receipts/',
        pattern='*.jpg',
        limit=100  # Process first 100 images
    )
    
    # Print statistics
    stats = results['statistics']
    print("\n=== Batch Statistics ===")
    print(f"Total processed: {stats['total_processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Avg processing time: {stats['avg_processing_time']:.2f}s")
    
    print("\n=== Field Statistics ===")
    for field in ['date', 'total', 'invoice_number']:
        print(f"{field}:")
        print(f"  Avg confidence: {stats['avg_confidence'][field]:.2f}")
        print(f"  Extraction rate: {stats['extraction_rate'][field]:.1%}")
    
    # Save results
    output_file = 'batch_results.json'
    with open(output_file, 'w') as f:
        json.dump(results['results'], f, indent=2)
    print(f"\nResults saved to {output_file}")
    
    # Print errors if any
    if results['errors']:
        print(f"\n=== Errors ({len(results['errors'])}) ===")
        for error in results['errors'][:5]:  # Show first 5
            print(f"  {error['image_id']}: {error['error']}")

if __name__ == '__main__':
    main()
