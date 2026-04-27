"""
Custom extraction example.

This example demonstrates how to use individual extractors
and customize extraction logic.
"""

from pipeline.extractor import DateExtractor, TotalExtractor, InvoiceNumberExtractor

def main():
    """Demonstrate custom extraction."""
    # Sample OCR text
    ocr_text = """
    ACME Store
    123 Main Street
    
    Invoice #: INV-2024-001
    Date: 15/01/2024
    
    Item 1: $10.00
    Item 2: $15.80
    
    Subtotal: $25.80
    Tax: $2.58
    Total: $28.38
    """
    
    # Initialize extractors
    date_extractor = DateExtractor()
    total_extractor = TotalExtractor()
    invoice_extractor = InvoiceNumberExtractor()
    
    # Extract fields
    print("Extracting fields...")
    
    date_result = date_extractor.extract(ocr_text)
    total_result = total_extractor.extract(ocr_text)
    invoice_result = invoice_extractor.extract(ocr_text)
    
    # Print results
    print("\n=== Extraction Results ===")
    print(f"Date: {date_result['value']} (confidence: {date_result['confidence']:.2f})")
    print(f"  Method: {date_result['method']}")
    print(f"  Candidates: {len(date_result['candidates'])}")
    
    print(f"\nTotal: ${total_result['value']:.2f} (confidence: {total_result['confidence']:.2f})")
    print(f"  Method: {total_result['method']}")
    print(f"  Candidates: {len(total_result['candidates'])}")
    
    print(f"\nInvoice: {invoice_result['value']} (confidence: {invoice_result['confidence']:.2f})")
    print(f"  Method: {invoice_result['method']}")
    print(f"  Candidates: {len(invoice_result['candidates'])}")
    
    # Show all candidates for total
    print("\n=== Total Candidates ===")
    for candidate in total_result['candidates'][:5]:  # Show top 5
        print(f"  ${candidate['value']:.2f} (score: {candidate['score']:.2f})")

if __name__ == '__main__':
    main()
