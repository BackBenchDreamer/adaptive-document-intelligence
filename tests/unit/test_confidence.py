"""
Unit tests for confidence scoring module.

Tests multi-factor scoring, calibration, and confidence management.
"""

import unittest
from datetime import datetime, timedelta
from pipeline.confidence import (
    MultiFactorConfidenceScorer,
    ConfidenceCalibrator,
    ConfidenceManager
)


class TestMultiFactorConfidenceScorer(unittest.TestCase):
    """Test multi-factor confidence scorer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scorer = MultiFactorConfidenceScorer()
    
    def test_initialization(self):
        """Test scorer initialization."""
        self.assertIsNotNone(self.scorer)
        self.assertEqual(self.scorer.weights['extraction'], 0.4)
        self.assertEqual(self.scorer.weights['ocr_quality'], 0.3)
        self.assertEqual(self.scorer.weights['validity'], 0.2)
        self.assertEqual(self.scorer.weights['pattern'], 0.1)
    
    def test_calculate_confidence_date(self):
        """Test confidence calculation for date field."""
        extraction_result = {
            'value': '2018-03-30',
            'confidence': 0.9,
            'raw_value': '30/03/2018'
        }
        ocr_result = {
            'text': 'Sample receipt text with date 30/03/2018',
            'confidence': 0.85
        }
        
        confidence, factors = self.scorer.calculate_confidence(
            extraction_result,
            ocr_result,
            'date'
        )
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertIn('extraction', factors)
        self.assertIn('ocr_quality', factors)
        self.assertIn('validity', factors)
        self.assertIn('pattern', factors)
    
    def test_calculate_confidence_total(self):
        """Test confidence calculation for total field."""
        extraction_result = {
            'value': 4.95,
            'confidence': 0.85,
            'raw_value': '$4.95'
        }
        ocr_result = {
            'text': 'Total: $4.95',
            'confidence': 0.9
        }
        
        confidence, factors = self.scorer.calculate_confidence(
            extraction_result,
            ocr_result,
            'total'
        )
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_calculate_confidence_invoice_number(self):
        """Test confidence calculation for invoice number."""
        extraction_result = {
            'value': 'INV-12345',
            'confidence': 0.8,
            'raw_value': 'INV-12345'
        }
        ocr_result = {
            'text': 'Invoice Number: INV-12345',
            'confidence': 0.88
        }
        
        confidence, factors = self.scorer.calculate_confidence(
            extraction_result,
            ocr_result,
            'invoice_number'
        )
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_ocr_quality_calculation(self):
        """Test OCR quality score calculation."""
        # High quality OCR
        ocr_result_high = {
            'text': 'A' * 500,
            'confidence': 0.95
        }
        quality_high = self.scorer._calculate_ocr_quality(ocr_result_high)
        self.assertGreater(quality_high, 0.8)
        
        # Low quality OCR
        ocr_result_low = {
            'text': 'AB',
            'confidence': 0.5
        }
        quality_low = self.scorer._calculate_ocr_quality(ocr_result_low)
        self.assertLess(quality_low, 0.6)
    
    def test_validate_date_valid(self):
        """Test date validation with valid dates."""
        # Valid recent date
        valid_date = '2023-06-15'
        score = self.scorer._validate_date(valid_date)
        self.assertEqual(score, 1.0)
        
        # Valid old date
        old_date = '2000-01-01'
        score = self.scorer._validate_date(old_date)
        self.assertEqual(score, 1.0)
    
    def test_validate_date_invalid(self):
        """Test date validation with invalid dates."""
        # Invalid year
        invalid_year = '1800-01-01'
        score = self.scorer._validate_date(invalid_year)
        self.assertEqual(score, 0.3)
        
        # Far future date
        future_date = (datetime.now() + timedelta(days=500)).isoformat()
        score = self.scorer._validate_date(future_date)
        self.assertEqual(score, 0.7)
    
    def test_validate_total_valid(self):
        """Test total validation with valid amounts."""
        # Normal amount
        score = self.scorer._validate_total(4.95)
        self.assertEqual(score, 1.0)
        
        # Large but valid amount
        score = self.scorer._validate_total(5000.50)
        self.assertEqual(score, 1.0)
    
    def test_validate_total_invalid(self):
        """Test total validation with invalid amounts."""
        # Negative amount
        score = self.scorer._validate_total(-10.0)
        self.assertEqual(score, 0.0)
        
        # Zero amount
        score = self.scorer._validate_total(0.0)
        self.assertEqual(score, 0.0)
        
        # Suspiciously round number
        score = self.scorer._validate_total(1000.0)
        self.assertEqual(score, 0.8)
        
        # Too large
        score = self.scorer._validate_total(200000.0)
        self.assertEqual(score, 0.5)
    
    def test_validate_invoice_number_valid(self):
        """Test invoice number validation with valid numbers."""
        # Standard format
        score = self.scorer._validate_invoice_number('INV-12345')
        self.assertEqual(score, 1.0)
        
        # Alphanumeric
        score = self.scorer._validate_invoice_number('ABC123XYZ')
        self.assertEqual(score, 1.0)
    
    def test_validate_invoice_number_invalid(self):
        """Test invoice number validation with invalid numbers."""
        # Too short
        score = self.scorer._validate_invoice_number('AB')
        self.assertEqual(score, 0.3)
        
        # Too long
        score = self.scorer._validate_invoice_number('A' * 35)
        self.assertEqual(score, 0.3)
        
        # No alphanumeric
        score = self.scorer._validate_invoice_number('---')
        self.assertEqual(score, 0.0)
    
    def test_date_pattern_strength(self):
        """Test date pattern matching."""
        # Strong pattern (DD/MM/YYYY)
        score = self.scorer._check_date_pattern('30/03/2018')
        self.assertEqual(score, 1.0)
        
        # ISO format
        score = self.scorer._check_date_pattern('2018-03-30')
        self.assertEqual(score, 0.95)
        
        # Weak pattern
        score = self.scorer._check_date_pattern('March 30, 2018')
        self.assertLess(score, 0.8)
    
    def test_total_pattern_strength(self):
        """Test total amount pattern matching."""
        # Strong pattern ($XX.XX)
        score = self.scorer._check_total_pattern('$4.95')
        self.assertEqual(score, 1.0)
        
        # Good pattern (XX.XX)
        score = self.scorer._check_total_pattern('4.95')
        self.assertEqual(score, 0.9)
        
        # With comma (matches second pattern first)
        score = self.scorer._check_total_pattern('$1,234.56')
        self.assertIn(score, [0.9, 0.95])  # Could match either pattern
    
    def test_invoice_pattern_strength(self):
        """Test invoice number pattern matching."""
        # Strong pattern (INV-XXX)
        score = self.scorer._check_invoice_pattern('INV-12345')
        self.assertEqual(score, 1.0)
        
        # Hash pattern
        score = self.scorer._check_invoice_pattern('#12345')
        self.assertEqual(score, 0.95)
        
        # Alphanumeric mix
        score = self.scorer._check_invoice_pattern('ABC123')
        self.assertGreaterEqual(score, 0.7)
    
    def test_confidence_bounds(self):
        """Test that confidence is always in [0, 1]."""
        # Test with extreme values
        extraction_result = {
            'value': 'test',
            'confidence': 1.5,  # Invalid, should be clamped
            'raw_value': 'test'
        }
        ocr_result = {
            'text': 'test',
            'confidence': 1.0
        }
        
        confidence, _ = self.scorer.calculate_confidence(
            extraction_result,
            ocr_result,
            'invoice_number'
        )
        
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_missing_values(self):
        """Test handling of missing values."""
        extraction_result = {
            'value': None,
            'confidence': 0.5,
            'raw_value': ''
        }
        ocr_result = {
            'text': '',
            'confidence': 0.5
        }
        
        confidence, factors = self.scorer.calculate_confidence(
            extraction_result,
            ocr_result,
            'date'
        )
        
        # Should still return valid confidence
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)


class TestConfidenceCalibrator(unittest.TestCase):
    """Test confidence calibrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calibrator = ConfidenceCalibrator()
    
    def test_initialization(self):
        """Test calibrator initialization."""
        self.assertIsNotNone(self.calibrator)
        self.assertFalse(self.calibrator.is_fitted)
        self.assertIn('date', self.calibrator.calibration_bins)
        self.assertIn('total', self.calibrator.calibration_bins)
        self.assertIn('invoice_number', self.calibrator.calibration_bins)
    
    def test_default_bins(self):
        """Test default calibration bins."""
        date_bins = self.calibrator._get_default_bins('date')
        self.assertIsInstance(date_bins, list)
        self.assertGreater(len(date_bins), 0)
        
        # Check bin structure
        for threshold, calibrated in date_bins:
            self.assertIsInstance(threshold, float)
            self.assertIsInstance(calibrated, float)
            self.assertGreaterEqual(threshold, 0.0)
            self.assertLessEqual(calibrated, 1.0)
    
    def test_calibrate_without_fitting(self):
        """Test calibration with default bins."""
        # Should use default bins
        calibrated = self.calibrator.calibrate(0.8, 'date')
        self.assertIsInstance(calibrated, float)
        self.assertGreaterEqual(calibrated, 0.0)
        self.assertLessEqual(calibrated, 1.0)
    
    def test_fit_calibrator(self):
        """Test fitting calibrator with data."""
        # Create mock predictions and ground truth
        predictions = [
            {
                'date': {'value': '2018-03-30', 'confidence': 0.9},
                'total': {'value': 4.95, 'confidence': 0.85},
                'invoice_number': {'value': 'INV-123', 'confidence': 0.8}
            },
            {
                'date': {'value': '2018-04-01', 'confidence': 0.7},
                'total': {'value': 10.50, 'confidence': 0.6},
                'invoice_number': {'value': 'INV-124', 'confidence': 0.75}
            },
            {
                'date': {'value': '2018-04-02', 'confidence': 0.5},
                'total': {'value': 15.00, 'confidence': 0.4},
                'invoice_number': {'value': 'INV-125', 'confidence': 0.5}
            }
        ]
        
        ground_truth = [
            {
                'date': '2018-03-30',
                'total': 4.95,
                'invoice_number': 'INV-123'
            },
            {
                'date': '2018-04-01',
                'total': 10.50,
                'invoice_number': 'INV-124'
            },
            {
                'date': '2018-04-03',  # Wrong date
                'total': 15.00,
                'invoice_number': 'INV-126'  # Wrong invoice
            }
        ]
        
        self.calibrator.fit(predictions, ground_truth)
        self.assertTrue(self.calibrator.is_fitted)
    
    def test_calibrate_after_fitting(self):
        """Test calibration after fitting."""
        # Fit with minimal data
        predictions = [
            {'date': {'value': '2018-03-30', 'confidence': 0.9}},
            {'date': {'value': '2018-04-01', 'confidence': 0.7}},
        ]
        ground_truth = [
            {'date': '2018-03-30'},
            {'date': '2018-04-01'},
        ]
        
        self.calibrator.fit(predictions, ground_truth)
        
        # Test calibration
        calibrated = self.calibrator.calibrate(0.8, 'date')
        self.assertIsInstance(calibrated, float)
        self.assertGreaterEqual(calibrated, 0.0)
        self.assertLessEqual(calibrated, 1.0)
    
    def test_bin_confidence(self):
        """Test confidence binning."""
        bins = [
            (0.0, 0.0),
            (0.5, 0.5),
            (0.8, 0.8),
            (0.9, 0.9)
        ]
        
        # Test exact match
        result = self.calibrator._bin_confidence(0.5, bins)
        self.assertAlmostEqual(result, 0.5, places=2)
        
        # Test interpolation
        result = self.calibrator._bin_confidence(0.65, bins)
        self.assertGreater(result, 0.5)
        self.assertLess(result, 0.8)
    
    def test_values_match(self):
        """Test value matching logic."""
        # Exact match
        self.assertTrue(
            self.calibrator._values_match('INV-123', 'INV-123', 'invoice_number')
        )
        
        # Case insensitive
        self.assertTrue(
            self.calibrator._values_match('inv-123', 'INV-123', 'invoice_number')
        )
        
        # Total with small difference
        self.assertTrue(
            self.calibrator._values_match(4.95, 4.95, 'total')
        )
        
        # Total with acceptable difference
        self.assertTrue(
            self.calibrator._values_match(4.95, 4.949, 'total')
        )
        
        # Total with large difference
        self.assertFalse(
            self.calibrator._values_match(4.95, 5.00, 'total')
        )


class TestConfidenceManager(unittest.TestCase):
    """Test confidence manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ConfidenceManager(use_calibration=False)
    
    def test_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.scorer)
        self.assertIsNotNone(self.manager.calibrator)
        self.assertFalse(self.manager.use_calibration)
    
    def test_initialization_with_calibration(self):
        """Test manager initialization with calibration."""
        manager = ConfidenceManager(use_calibration=True)
        self.assertTrue(manager.use_calibration)
    
    def test_score_extraction(self):
        """Test scoring extraction results."""
        extraction_results = {
            'date': {
                'value': '2018-03-30',
                'confidence': 0.9,
                'raw_value': '30/03/2018'
            },
            'total': {
                'value': 4.95,
                'confidence': 0.85,
                'raw_value': '$4.95'
            },
            'invoice_number': {
                'value': 'INV-12345',
                'confidence': 0.8,
                'raw_value': 'INV-12345'
            }
        }
        
        ocr_result = {
            'text': 'Receipt with date 30/03/2018 and total $4.95',
            'confidence': 0.88
        }
        
        scored_results = self.manager.score_extraction(
            extraction_results,
            ocr_result
        )
        
        # Check structure
        self.assertIn('date', scored_results)
        self.assertIn('total', scored_results)
        self.assertIn('invoice_number', scored_results)
        self.assertIn('metadata', scored_results)
        
        # Check date field
        date_result = scored_results['date']
        self.assertIn('value', date_result)
        self.assertIn('confidence', date_result)
        self.assertIn('raw_confidence', date_result)
        self.assertIn('confidence_factors', date_result)
        
        # Check confidence values
        self.assertIsInstance(date_result['confidence'], float)
        self.assertGreaterEqual(date_result['confidence'], 0.0)
        self.assertLessEqual(date_result['confidence'], 1.0)
        
        # Check factors
        factors = date_result['confidence_factors']
        self.assertIn('extraction', factors)
        self.assertIn('ocr_quality', factors)
        self.assertIn('validity', factors)
        self.assertIn('pattern', factors)
        
        # Check metadata
        metadata = scored_results['metadata']
        self.assertIn('calibration_applied', metadata)
        self.assertIn('scoring_time', metadata)
        self.assertFalse(metadata['calibration_applied'])
    
    def test_score_extraction_with_calibration(self):
        """Test scoring with calibration enabled."""
        # Create manager with calibration
        calibrator = ConfidenceCalibrator()
        manager = ConfidenceManager(
            use_calibration=True,
            calibrator=calibrator
        )
        
        # Fit calibrator with minimal data
        predictions = [
            {'date': {'value': '2018-03-30', 'confidence': 0.9}}
        ]
        ground_truth = [
            {'date': '2018-03-30'}
        ]
        calibrator.fit(predictions, ground_truth)
        
        extraction_results = {
            'date': {
                'value': '2018-03-30',
                'confidence': 0.9,
                'raw_value': '30/03/2018'
            }
        }
        
        ocr_result = {
            'text': 'Date: 30/03/2018',
            'confidence': 0.85
        }
        
        scored_results = manager.score_extraction(
            extraction_results,
            ocr_result
        )
        
        # Should have calibration applied
        self.assertTrue(scored_results['metadata']['calibration_applied'])
    
    def test_score_extraction_empty(self):
        """Test scoring with empty extraction results."""
        extraction_results = {}
        ocr_result = {'text': '', 'confidence': 0.5}
        
        scored_results = self.manager.score_extraction(
            extraction_results,
            ocr_result
        )
        
        # Should only have metadata
        self.assertIn('metadata', scored_results)
        self.assertEqual(len(scored_results), 1)
    
    def test_score_extraction_partial(self):
        """Test scoring with partial extraction results."""
        extraction_results = {
            'date': {
                'value': '2018-03-30',
                'confidence': 0.9,
                'raw_value': '30/03/2018'
            }
            # Missing total and invoice_number
        }
        
        ocr_result = {
            'text': 'Date: 30/03/2018',
            'confidence': 0.85
        }
        
        scored_results = self.manager.score_extraction(
            extraction_results,
            ocr_result
        )
        
        # Should have date and metadata only
        self.assertIn('date', scored_results)
        self.assertNotIn('total', scored_results)
        self.assertNotIn('invoice_number', scored_results)
        self.assertIn('metadata', scored_results)


if __name__ == '__main__':
    unittest.main()

# Made with Bob
