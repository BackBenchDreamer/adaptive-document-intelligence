"""
Unit Tests for Evaluation Module.

Tests the metrics calculation, confidence calibration analysis,
and evaluation functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from tests.metrics.evaluation import (
    MetricsCalculator,
    ConfidenceCalibrationAnalyzer,
    DocumentEvaluator
)


class TestMetricsCalculator(unittest.TestCase):
    """Test MetricsCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = MetricsCalculator()
    
    def test_calculate_accuracy_perfect(self):
        """Test accuracy calculation with perfect predictions."""
        predictions = ['a', 'b', 'c', 'd']
        ground_truth = ['a', 'b', 'c', 'd']
        
        accuracy = self.calculator.calculate_accuracy(predictions, ground_truth)
        self.assertEqual(accuracy, 1.0)
    
    def test_calculate_accuracy_partial(self):
        """Test accuracy calculation with partial matches."""
        predictions = ['a', 'b', 'x', 'd']
        ground_truth = ['a', 'b', 'c', 'd']
        
        accuracy = self.calculator.calculate_accuracy(predictions, ground_truth)
        self.assertEqual(accuracy, 0.75)  # 3 out of 4 correct
    
    def test_calculate_accuracy_empty(self):
        """Test accuracy calculation with empty lists."""
        accuracy = self.calculator.calculate_accuracy([], [])
        self.assertEqual(accuracy, 0.0)
    
    def test_calculate_accuracy_length_mismatch(self):
        """Test accuracy calculation with mismatched lengths."""
        predictions = ['a', 'b']
        ground_truth = ['a', 'b', 'c']
        
        accuracy = self.calculator.calculate_accuracy(predictions, ground_truth)
        self.assertEqual(accuracy, 0.0)
    
    def test_precision_recall_f1_perfect(self):
        """Test precision/recall/F1 with perfect predictions."""
        predictions = ['a', 'b', 'c']
        ground_truth = ['a', 'b', 'c']
        
        precision, recall, f1 = self.calculator.calculate_precision_recall_f1(
            predictions, ground_truth
        )
        
        self.assertEqual(precision, 1.0)
        self.assertEqual(recall, 1.0)
        self.assertEqual(f1, 1.0)
    
    def test_precision_recall_f1_with_errors(self):
        """Test precision/recall/F1 with some errors."""
        predictions = ['a', 'b', 'x', None]  # 2 correct, 1 wrong, 1 missing
        ground_truth = ['a', 'b', 'c', 'd']
        
        precision, recall, f1 = self.calculator.calculate_precision_recall_f1(
            predictions, ground_truth
        )
        
        # TP=2, FP=1, FN=2
        # Precision = 2/(2+1) = 0.667
        # Recall = 2/(2+2) = 0.5
        # F1 = 2*0.667*0.5/(0.667+0.5) = 0.571
        self.assertAlmostEqual(precision, 0.667, places=2)
        self.assertAlmostEqual(recall, 0.5, places=2)
        self.assertAlmostEqual(f1, 0.571, places=2)
    
    def test_fuzzy_match_exact(self):
        """Test fuzzy matching with exact matches."""
        predictions = ['hello', 'world']
        ground_truth = ['hello', 'world']
        
        fuzzy = self.calculator.calculate_fuzzy_match(
            predictions, ground_truth, threshold=0.8
        )
        self.assertEqual(fuzzy, 1.0)
    
    def test_fuzzy_match_similar(self):
        """Test fuzzy matching with similar strings."""
        predictions = ['hello', 'wrld']  # 'wrld' is similar to 'world'
        ground_truth = ['hello', 'world']
        
        fuzzy = self.calculator.calculate_fuzzy_match(
            predictions, ground_truth, threshold=0.7
        )
        # 'hello' matches exactly, 'wrld' is similar enough
        self.assertGreater(fuzzy, 0.5)
    
    def test_date_accuracy_exact(self):
        """Test date accuracy with exact matches."""
        predictions = ['2018-03-30', '2018-04-15']
        ground_truth = ['2018-03-30', '2018-04-15']
        
        accuracy = self.calculator.calculate_date_accuracy(
            predictions, ground_truth, tolerance_days=0
        )
        self.assertEqual(accuracy, 1.0)
    
    def test_date_accuracy_with_tolerance(self):
        """Test date accuracy with tolerance."""
        predictions = ['2018-03-30', '2018-04-16']  # Second date off by 1 day
        ground_truth = ['2018-03-30', '2018-04-15']
        
        # Should fail with 0 tolerance
        accuracy_strict = self.calculator.calculate_date_accuracy(
            predictions, ground_truth, tolerance_days=0
        )
        self.assertEqual(accuracy_strict, 0.5)
        
        # Should pass with 1 day tolerance
        accuracy_tolerant = self.calculator.calculate_date_accuracy(
            predictions, ground_truth, tolerance_days=1
        )
        self.assertEqual(accuracy_tolerant, 1.0)
    
    def test_amount_accuracy_exact(self):
        """Test amount accuracy with exact matches."""
        predictions = [10.50, 25.99]
        ground_truth = [10.50, 25.99]
        
        accuracy = self.calculator.calculate_amount_accuracy(
            predictions, ground_truth, tolerance_percent=0.0
        )
        self.assertEqual(accuracy, 1.0)
    
    def test_amount_accuracy_with_tolerance(self):
        """Test amount accuracy with tolerance."""
        predictions = [10.50, 26.00]  # Second amount slightly off
        ground_truth = [10.50, 25.99]
        
        # Should fail with 0% tolerance
        accuracy_strict = self.calculator.calculate_amount_accuracy(
            predictions, ground_truth, tolerance_percent=0.0
        )
        self.assertEqual(accuracy_strict, 0.5)
        
        # Should pass with 1% tolerance (26.00 is within 1% of 25.99)
        accuracy_tolerant = self.calculator.calculate_amount_accuracy(
            predictions, ground_truth, tolerance_percent=0.01
        )
        self.assertEqual(accuracy_tolerant, 1.0)


class TestConfidenceCalibrationAnalyzer(unittest.TestCase):
    """Test ConfidenceCalibrationAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = ConfidenceCalibrationAnalyzer()
    
    def test_analyze_calibration_perfect(self):
        """Test calibration analysis with perfectly calibrated predictions."""
        # Create perfectly calibrated data:
        # Low confidence (0.3) -> 30% accuracy
        # High confidence (0.9) -> 90% accuracy
        predictions = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        ground_truth = ['a', 'x', 'x', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        confidences = [0.3, 0.3, 0.3, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
        
        result = self.analyzer.analyze_calibration(
            predictions, ground_truth, confidences, 'test_field'
        )
        
        self.assertIn('by_bucket', result)
        self.assertIn('expected_calibration_error', result)
        self.assertIn('is_well_calibrated', result)
        
        # Should have low ECE for well-calibrated data
        self.assertLess(result['expected_calibration_error'], 0.2)
    
    def test_analyze_calibration_overconfident(self):
        """Test calibration analysis with overconfident predictions."""
        # High confidence but low accuracy
        predictions = ['a', 'b', 'c', 'd', 'e']
        ground_truth = ['x', 'x', 'x', 'x', 'x']  # All wrong
        confidences = [0.95, 0.95, 0.95, 0.95, 0.95]  # But high confidence
        
        result = self.analyzer.analyze_calibration(
            predictions, ground_truth, confidences, 'test_field'
        )
        
        # Should have high ECE for poorly calibrated data
        self.assertGreater(result['expected_calibration_error'], 0.5)
        self.assertFalse(result['is_well_calibrated'])
    
    def test_calculate_ece(self):
        """Test ECE calculation."""
        predictions = ['a', 'b', 'c', 'd']
        ground_truth = ['a', 'b', 'x', 'x']
        confidences = [0.9, 0.9, 0.9, 0.9]
        
        ece = self.analyzer.calculate_ece(predictions, ground_truth, confidences)
        
        # ECE should be positive (confidence 0.9 but accuracy 0.5)
        self.assertGreater(ece, 0.0)
        self.assertLess(ece, 1.0)
    
    def test_empty_calibration(self):
        """Test calibration with empty data."""
        result = self.analyzer.analyze_calibration([], [], [], 'test_field')
        
        self.assertEqual(result['expected_calibration_error'], 1.0)
        self.assertFalse(result['is_well_calibrated'])


class TestDocumentEvaluator(unittest.TestCase):
    """Test DocumentEvaluator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_processor = Mock()
        self.evaluator = DocumentEvaluator(self.mock_processor)
    
    @patch('tests.metrics.evaluation.SROIEDataLoader')
    def test_evaluate_dataset_basic(self, mock_loader_class):
        """Test basic dataset evaluation."""
        # Mock data loader
        mock_loader = Mock()
        mock_loader.load_dataset.return_value = [
            {
                'image_path': 'test1.jpg',
                'entities': {'date': '2018-03-30', 'total': 10.50}
            },
            {
                'image_path': 'test2.jpg',
                'entities': {'date': '2018-04-15', 'total': 25.99}
            }
        ]
        mock_loader_class.return_value = mock_loader
        
        # Mock processor results
        self.mock_processor.process_document.side_effect = [
            {
                'success': True,
                'extracted_entities': {'date': '2018-03-30', 'total': 10.50},
                'confidence_scores': {'date': 0.9, 'total': 0.85}
            },
            {
                'success': True,
                'extracted_entities': {'date': '2018-04-15', 'total': 25.99},
                'confidence_scores': {'date': 0.95, 'total': 0.90}
            }
        ]
        
        # Run evaluation
        results = self.evaluator.evaluate_dataset(split='train', limit=2)
        
        # Check results structure
        self.assertIn('overall', results)
        self.assertIn('per_field', results)
        self.assertIn('confidence_analysis', results)
        self.assertIn('samples_evaluated', results)
        self.assertIn('processing_time', results)
        
        # Check that we evaluated 2 samples
        self.assertEqual(results['samples_evaluated'], 2)
        
        # Check that accuracy is perfect (both predictions correct)
        self.assertEqual(results['overall']['accuracy'], 1.0)
    
    def test_evaluate_field(self):
        """Test single field evaluation."""
        predictions = ['a', 'b', 'c', 'd']
        ground_truth = ['a', 'b', 'c', 'd']
        confidences = [0.9, 0.85, 0.95, 0.88]
        
        result = self.evaluator.evaluate_field(
            predictions, ground_truth, confidences, 'test_field'
        )
        
        self.assertIn('accuracy', result)
        self.assertIn('precision', result)
        self.assertIn('recall', result)
        self.assertIn('f1', result)
        self.assertIn('extraction_rate', result)
        
        # Perfect predictions should have 1.0 accuracy
        self.assertEqual(result['accuracy'], 1.0)


if __name__ == '__main__':
    unittest.main()


# Made with Bob