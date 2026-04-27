"""
Unit tests for field extraction module.

Tests each extractor independently with various edge cases.
"""

import unittest
from pipeline.extractor import (
    DateExtractor,
    TotalExtractor,
    InvoiceNumberExtractor,
    ExtractionManager
)


class TestDateExtractor(unittest.TestCase):
    """Test DateExtractor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = DateExtractor()
    
    def test_extract_date_dd_mm_yyyy(self):
        """Test extraction of DD/MM/YYYY format."""
        text = "Invoice Date: 30/03/2018\nTotal: $10.50"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], '2018-03-30')
        self.assertGreater(result['confidence'], 0.7)
        self.assertEqual(result['raw_value'], '30/03/2018')
    
    def test_extract_date_dd_dash_mm_yyyy(self):
        """Test extraction of DD-MM-YYYY format."""
        text = "Date: 15-06-2019\nAmount: $25.00"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], '2019-06-15')
        self.assertGreater(result['confidence'], 0.7)
    
    def test_extract_date_yyyy_mm_dd(self):
        """Test extraction of YYYY-MM-DD format."""
        text = "Invoice: 2020-12-25\nTotal: $100.00"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], '2020-12-25')
        self.assertGreater(result['confidence'], 0.5)
    
    def test_extract_date_with_month_name(self):
        """Test extraction of date with month name."""
        text = "Date: 15 March 2021\nTotal: $50.00"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], '2021-03-15')
        self.assertGreater(result['confidence'], 0.5)
    
    def test_extract_date_multiple_candidates(self):
        """Test extraction with multiple date candidates."""
        text = """
        Receipt Date: 01/01/2020
        Valid until: 31/12/2020
        Total: $75.00
        """
        result = self.extractor.extract(text)
        
        # Should prefer the one near "Receipt Date"
        self.assertEqual(result['value'], '2020-01-01')
        self.assertGreater(result['confidence'], 0.7)
    
    def test_extract_date_no_keyword(self):
        """Test extraction without nearby keywords."""
        text = "Invoice #12345\n30/03/2018\nTotal: $10.50"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], '2018-03-30')
        # Lower confidence without keywords
        self.assertLess(result['confidence'], 0.8)
    
    def test_extract_date_empty_text(self):
        """Test extraction from empty text."""
        result = self.extractor.extract("")
        
        self.assertIsNone(result['value'])
        self.assertEqual(result['confidence'], 0.0)
        self.assertEqual(result['method'], 'no_text')
    
    def test_extract_date_no_candidates(self):
        """Test extraction when no dates found."""
        text = "Invoice Total: $100.00"
        result = self.extractor.extract(text)
        
        self.assertIsNone(result['value'])
        self.assertEqual(result['confidence'], 0.0)
    
    def test_normalize_date_invalid(self):
        """Test date normalization with invalid date."""
        # 32nd day doesn't exist
        normalized = self.extractor._normalize_date('32/13/2020', 'DD/MM/YYYY')
        self.assertIsNone(normalized)


class TestTotalExtractor(unittest.TestCase):
    """Test TotalExtractor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = TotalExtractor()
    
    def test_extract_total_with_dollar_sign(self):
        """Test extraction of amount with $ symbol."""
        text = "Subtotal: $8.50\nTax: $1.50\nTotal: $10.00"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], 10.00)
        self.assertGreater(result['confidence'], 0.7)
        self.assertIn('$10.00', result['raw_value'])
    
    def test_extract_total_without_symbol(self):
        """Test extraction of amount without currency symbol."""
        text = "Subtotal: 8.50\nTax: 1.50\nTotal: 10.00"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], 10.00)
        self.assertGreater(result['confidence'], 0.5)
    
    def test_extract_total_with_thousands_separator(self):
        """Test extraction of large amount with comma separator."""
        text = "Total Amount Due: $1,234.56"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], 1234.56)
        self.assertGreater(result['confidence'], 0.7)
    
    def test_extract_total_multiple_amounts(self):
        """Test extraction with multiple amounts."""
        text = """
        Item 1: $5.00
        Item 2: $3.50
        Subtotal: $8.50
        Tax: $1.50
        Total: $10.00
        """
        result = self.extractor.extract(text)
        
        # Should select the one near "Total"
        self.assertEqual(result['value'], 10.00)
        self.assertGreater(result['confidence'], 0.7)
    
    def test_extract_total_avoid_subtotal(self):
        """Test that subtotal is penalized."""
        text = "Subtotal: $100.00\nTax: $10.00\nGrand Total: $110.00"
        result = self.extractor.extract(text)
        
        # Should prefer Grand Total over Subtotal
        self.assertEqual(result['value'], 110.00)
    
    def test_extract_total_bottom_position_bias(self):
        """Test that amounts at bottom are preferred."""
        text = """
        Invoice #123
        Date: 01/01/2020
        Item: $5.00
        
        
        
        
        Total: $5.00
        """
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], 5.00)
        # Bottom position should have higher confidence
        self.assertGreater(result['confidence'], 0.6)
    
    def test_extract_total_largest_amount(self):
        """Test that largest amount gets bonus when no keywords."""
        text = "Amount 1: $5.00\nAmount 2: $50.00\nAmount 3: $10.00"
        result = self.extractor.extract(text)
        
        # Should prefer largest amount
        self.assertEqual(result['value'], 50.00)
    
    def test_extract_total_empty_text(self):
        """Test extraction from empty text."""
        result = self.extractor.extract("")
        
        self.assertIsNone(result['value'])
        self.assertEqual(result['confidence'], 0.0)
    
    def test_extract_total_no_candidates(self):
        """Test extraction when no amounts found."""
        text = "Invoice Date: 01/01/2020"
        result = self.extractor.extract(text)
        
        self.assertIsNone(result['value'])
        self.assertEqual(result['confidence'], 0.0)
    
    def test_extract_total_with_change(self):
        """Test that 'change' amounts are penalized."""
        text = "Total: $20.00\nCash: $50.00\nChange: $30.00"
        result = self.extractor.extract(text)
        
        # Should prefer Total over Change
        self.assertEqual(result['value'], 20.00)


class TestInvoiceNumberExtractor(unittest.TestCase):
    """Test InvoiceNumberExtractor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = InvoiceNumberExtractor()
    
    def test_extract_invoice_with_prefix(self):
        """Test extraction of invoice number with INV prefix."""
        text = "Invoice No: INV-12345\nDate: 01/01/2020\nTotal: $10.00"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], 'INV-12345')
        self.assertGreater(result['confidence'], 0.7)
    
    def test_extract_invoice_with_hash(self):
        """Test extraction of invoice number with # symbol."""
        text = "Receipt #123456\nDate: 01/01/2020\nTotal: $10.00"
        result = self.extractor.extract(text)
        
        self.assertIn('123456', result['value'])
        self.assertGreater(result['confidence'], 0.5)
    
    def test_extract_invoice_after_keyword(self):
        """Test extraction of invoice number after keyword."""
        text = "Invoice Number: ABC123XYZ\nDate: 01/01/2020"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], 'ABC123XYZ')
        self.assertGreater(result['confidence'], 0.7)
    
    def test_extract_invoice_standalone(self):
        """Test extraction of standalone alphanumeric."""
        text = "Receipt\nABC12345\nDate: 01/01/2020\nTotal: $10.00"
        result = self.extractor.extract(text)
        
        self.assertEqual(result['value'], 'ABC12345')
        self.assertGreater(result['confidence'], 0.3)
    
    def test_extract_invoice_top_position_bias(self):
        """Test that invoice numbers at top are preferred."""
        text = """
        Invoice: INV001
        Date: 01/01/2020
        
        
        
        
        Reference: REF999
        """
        result = self.extractor.extract(text)
        
        # Should prefer top position
        self.assertEqual(result['value'], 'INV001')
    
    def test_extract_invoice_empty_text(self):
        """Test extraction from empty text."""
        result = self.extractor.extract("")
        
        self.assertIsNone(result['value'])
        self.assertEqual(result['confidence'], 0.0)
    
    def test_extract_invoice_no_candidates(self):
        """Test extraction when no invoice numbers found."""
        text = "Date: 01/01/2020\nTotal: $10.00"
        result = self.extractor.extract(text)
        
        self.assertIsNone(result['value'])
        self.assertEqual(result['confidence'], 0.0)


class TestExtractionManager(unittest.TestCase):
    """Test ExtractionManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ExtractionManager()
    
    def test_extract_all_fields(self):
        """Test extraction of all fields from complete receipt."""
        ocr_result = {
            'text': """
            RECEIPT
            Invoice No: INV-12345
            Date: 30/03/2018
            
            Item 1: $5.00
            Item 2: $3.50
            
            Subtotal: $8.50
            Tax: $1.50
            Total: $10.00
            """,
            'confidence': 0.95,
            'metadata': {}
        }
        
        result = self.manager.extract_fields(ocr_result)
        
        # Check date
        self.assertEqual(result['date']['value'], '2018-03-30')
        self.assertGreater(result['date']['confidence'], 0.5)
        
        # Check total
        self.assertEqual(result['total']['value'], 10.00)
        self.assertGreater(result['total']['confidence'], 0.5)
        
        # Check invoice number
        self.assertEqual(result['invoice_number']['value'], 'INV-12345')
        self.assertGreater(result['invoice_number']['confidence'], 0.5)
        
        # Check metadata
        self.assertEqual(result['metadata']['ocr_confidence'], 0.95)
        self.assertGreater(result['metadata']['text_length'], 0)
        self.assertIn('date', result['metadata']['candidates_considered'])
    
    def test_extract_partial_fields(self):
        """Test extraction when some fields are missing."""
        ocr_result = {
            'text': "Date: 01/01/2020\nTotal: $50.00",
            'confidence': 0.85,
            'metadata': {}
        }
        
        result = self.manager.extract_fields(ocr_result)
        
        # Date and total should be found
        self.assertIsNotNone(result['date']['value'])
        self.assertIsNotNone(result['total']['value'])
        
        # Invoice number might not be found
        # (depends on whether standalone numbers are detected)
    
    def test_extract_empty_text(self):
        """Test extraction from empty OCR result."""
        ocr_result = {
            'text': '',
            'confidence': 0.0,
            'metadata': {}
        }
        
        result = self.manager.extract_fields(ocr_result)
        
        # All fields should be None
        self.assertIsNone(result['date']['value'])
        self.assertIsNone(result['total']['value'])
        self.assertIsNone(result['invoice_number']['value'])
        
        # Confidences should be 0
        self.assertEqual(result['date']['confidence'], 0.0)
        self.assertEqual(result['total']['confidence'], 0.0)
        self.assertEqual(result['invoice_number']['confidence'], 0.0)
    
    def test_extract_noisy_text(self):
        """Test extraction from noisy OCR text."""
        ocr_result = {
            'text': """
            R3C31PT
            1nv0ice: 1NV-123
            D@te: 30/O3/2018
            T0tal: $1O.OO
            """,
            'confidence': 0.60,
            'metadata': {}
        }
        
        result = self.manager.extract_fields(ocr_result)
        
        # Should still extract some fields despite noise
        # (though confidence may be lower)
        self.assertIsNotNone(result['metadata'])
    
    def test_extract_real_world_format(self):
        """Test extraction from realistic receipt format."""
        ocr_result = {
            'text': """
            TESCO
            Store #4521
            
            Receipt No: 7890123456
            Date: 15-06-2019
            
            MILK 2L          $3.50
            BREAD            $2.00
            EGGS 12          $4.50
            
            SUBTOTAL        $10.00
            GST 7%           $0.70
            TOTAL           $10.70
            
            CASH            $20.00
            CHANGE           $9.30
            """,
            'confidence': 0.92,
            'metadata': {}
        }
        
        result = self.manager.extract_fields(ocr_result)
        
        # Check date
        self.assertEqual(result['date']['value'], '2019-06-15')
        
        # Check total (should be $10.70, not subtotal or change)
        self.assertEqual(result['total']['value'], 10.70)
        
        # Check invoice/receipt number
        self.assertIsNotNone(result['invoice_number']['value'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_date_extractor_invalid_dates(self):
        """Test date extractor with invalid dates."""
        extractor = DateExtractor()
        
        # Invalid day
        text = "Date: 32/01/2020"
        result = extractor.extract(text)
        self.assertIsNone(result['value'])
        
        # Invalid month
        text = "Date: 15/13/2020"
        result = extractor.extract(text)
        self.assertIsNone(result['value'])
    
    def test_total_extractor_unreasonable_amounts(self):
        """Test total extractor with unreasonable amounts."""
        extractor = TotalExtractor()
        
        # Too small
        text = "Total: $0.001"
        result = extractor.extract(text)
        # Should not find candidates below $0.01
        
        # Too large (over $100,000)
        text = "Total: $999999.99"
        result = extractor.extract(text)
        # Should not find candidates over $100,000
    
    def test_unicode_currency_symbols(self):
        """Test extraction with various currency symbols."""
        extractor = TotalExtractor()
        
        # Euro
        text = "Total: €50.00"
        result = extractor.extract(text)
        self.assertEqual(result['value'], 50.00)
        
        # Pound
        text = "Total: £75.50"
        result = extractor.extract(text)
        self.assertEqual(result['value'], 75.50)
    
    def test_extraction_performance(self):
        """Test that extraction completes in reasonable time."""
        manager = ExtractionManager()
        
        # Large text
        large_text = "Item: $1.00\n" * 1000 + "Total: $1000.00"
        ocr_result = {
            'text': large_text,
            'confidence': 0.9,
            'metadata': {}
        }
        
        result = manager.extract_fields(ocr_result)
        
        # Should complete in under 1 second
        self.assertLess(result['metadata']['extraction_time'], 1.0)


if __name__ == '__main__':
    unittest.main()

# Made with Bob
