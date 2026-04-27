"""
Batch processing example.

This example demonstrates how to process multiple documents
in a directory and save results to a file.
"""

from pipeline.pipeline import DocumentProcessor
from pathlib import Path
import json

def main():
    """Process a batch of documents."""
    # Initialize processor
    processor = DocumentProcessor(ocr_engine='tesseract')
    
    # Get list of images
    image_dir = Path('path/to/receipts/')
    image_paths = [str(p) for p in image_dir.glob('*.jpg')][:100]  # First 100 images
    
    # Process batch
    print("Processing batch...")
    results = processor.process_batch(
        image_paths=image_paths,
        show_progress=True
    )
    
    # Calculate statistics
    stats = processor.get_statistics(results)
    
    # Print statistics
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
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")
    
    # Show errors if any
    failed = [r for r in results if not r.get('metadata', {}).get('success', False)]
    if failed:
        print(f"\n=== Errors ({len(failed)}) ===")
        for error in failed[:5]:  # Show first 5
            print(f"  {error['image_path']}: {error['metadata'].get('error', 'Unknown error')}")

if __name__ == '__main__':
    main()
