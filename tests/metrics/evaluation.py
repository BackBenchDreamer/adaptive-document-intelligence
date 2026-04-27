"""
Evaluation Module for Adaptive Document Intelligence System.

This module provides comprehensive evaluation capabilities for measuring
system performance on the SROIE dataset. It includes:
- Accuracy metrics (precision, recall, F1)
- Confidence calibration analysis
- Per-field performance tracking
- Detailed error analysis

Design Philosophy:
- Comprehensive: Multiple metrics for thorough evaluation
- Calibrated: Analyze confidence score quality
- Actionable: Provide insights for improvement
- Efficient: Cache results and batch processing
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from difflib import SequenceMatcher

from core.logging_config import get_logger
from tests.data.sroie_loader import SROIEDataLoader
from pipeline.pipeline import DocumentProcessor

# Module logger
logger = get_logger(__name__)


class MetricsCalculator:
    """
    Calculate various evaluation metrics.
    
    Provides static methods for computing accuracy, precision, recall, F1,
    and specialized metrics for dates and amounts.
    """
    
    @staticmethod
    def calculate_accuracy(
        predictions: List[Any],
        ground_truth: List[Any]
    ) -> float:
        """
        Calculate accuracy (exact match rate).
        
        Args:
            predictions: List of predicted values
            ground_truth: List of ground truth values
            
        Returns:
            Accuracy score [0, 1]
        """
        if not predictions or not ground_truth:
            return 0.0
        
        if len(predictions) != len(ground_truth):
            logger.warning(
                f"Length mismatch: predictions={len(predictions)}, "
                f"ground_truth={len(ground_truth)}"
            )
            return 0.0
        
        correct = sum(
            1 for pred, truth in zip(predictions, ground_truth)
            if pred == truth
        )
        
        return correct / len(predictions)
    
    @staticmethod
    def calculate_precision_recall_f1(
        predictions: List[Any],
        ground_truth: List[Any]
    ) -> Tuple[float, float, float]:
        """
        Calculate precision, recall, and F1 score.
        
        For information extraction:
        - True Positive: Correct extraction
        - False Positive: Incorrect extraction
        - False Negative: Missing extraction
        
        Args:
            predictions: List of predicted values
            ground_truth: List of ground truth values
            
        Returns:
            Tuple of (precision, recall, f1)
        """
        if not ground_truth:
            return 0.0, 0.0, 0.0
        
        # Count true positives, false positives, false negatives
        tp = 0  # Correct extractions
        fp = 0  # Incorrect extractions
        fn = 0  # Missing extractions
        
        for pred, truth in zip(predictions, ground_truth):
            if truth is None or truth == '':
                # No ground truth
                if pred is not None and pred != '':
                    fp += 1  # Extracted when shouldn't
            else:
                # Ground truth exists
                if pred is None or pred == '':
                    fn += 1  # Failed to extract
                elif pred == truth:
                    tp += 1  # Correct extraction
                else:
                    fp += 1  # Incorrect extraction
        
        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        
        return precision, recall, f1
    
    @staticmethod
    def calculate_fuzzy_match(
        predictions: List[str],
        ground_truth: List[str],
        threshold: float = 0.8
    ) -> float:
        """
        Calculate fuzzy string matching accuracy.
        
        Uses SequenceMatcher for similarity comparison.
        Useful for cases where exact match is too strict.
        
        Args:
            predictions: List of predicted strings
            ground_truth: List of ground truth strings
            threshold: Similarity threshold [0, 1]
            
        Returns:
            Fuzzy match accuracy [0, 1]
        """
        if not predictions or not ground_truth:
            return 0.0
        
        if len(predictions) != len(ground_truth):
            return 0.0
        
        matches = 0
        for pred, truth in zip(predictions, ground_truth):
            if pred is None or truth is None:
                continue
            
            # Calculate similarity ratio
            similarity = SequenceMatcher(None, str(pred), str(truth)).ratio()
            
            if similarity >= threshold:
                matches += 1
        
        return matches / len(predictions)
    
    @staticmethod
    def calculate_date_accuracy(
        predictions: List[str],
        ground_truth: List[str],
        tolerance_days: int = 0
    ) -> float:
        """
        Calculate date accuracy with optional tolerance.
        
        Parses dates and allows for N days difference.
        
        Args:
            predictions: List of predicted date strings
            ground_truth: List of ground truth date strings
            tolerance_days: Allow N days difference
            
        Returns:
            Date accuracy [0, 1]
        """
        if not predictions or not ground_truth:
            return 0.0
        
        if len(predictions) != len(ground_truth):
            return 0.0
        
        correct = 0
        for pred, truth in zip(predictions, ground_truth):
            if pred is None or truth is None:
                continue
            
            try:
                # Try to parse dates
                pred_date = datetime.strptime(pred, '%Y-%m-%d')
                truth_date = datetime.strptime(truth, '%Y-%m-%d')
                
                # Check if within tolerance
                diff_days = abs((pred_date - truth_date).days)
                if diff_days <= tolerance_days:
                    correct += 1
            except (ValueError, TypeError):
                # If parsing fails, check exact match
                if pred == truth:
                    correct += 1
        
        return correct / len(predictions)
    
    @staticmethod
    def calculate_amount_accuracy(
        predictions: List[float],
        ground_truth: List[float],
        tolerance_percent: float = 0.01
    ) -> float:
        """
        Calculate amount accuracy with tolerance.
        
        Allows for small percentage differences (e.g., rounding).
        
        Args:
            predictions: List of predicted amounts
            ground_truth: List of ground truth amounts
            tolerance_percent: Allow N% difference (e.g., 0.01 = 1%)
            
        Returns:
            Amount accuracy [0, 1]
        """
        if not predictions or not ground_truth:
            return 0.0
        
        if len(predictions) != len(ground_truth):
            return 0.0
        
        correct = 0
        for pred, truth in zip(predictions, ground_truth):
            if pred is None or truth is None:
                continue
            
            try:
                pred_val = float(pred)
                truth_val = float(truth)
                
                # Check if within tolerance
                if truth_val == 0:
                    if pred_val == 0:
                        correct += 1
                else:
                    diff_percent = abs(pred_val - truth_val) / truth_val
                    if diff_percent <= tolerance_percent:
                        correct += 1
            except (ValueError, TypeError):
                # If conversion fails, check exact match
                if pred == truth:
                    correct += 1
        
        return correct / len(predictions)


class ConfidenceCalibrationAnalyzer:
    """
    Analyze confidence calibration.
    
    Checks if confidence scores correlate with actual accuracy.
    Well-calibrated systems have high confidence predictions that
    are actually more accurate.
    """
    
    def __init__(self):
        """Initialize analyzer with confidence buckets."""
        self.confidence_buckets = [
            (0.0, 0.3, 'very_low'),
            (0.3, 0.6, 'low'),
            (0.6, 0.8, 'medium'),
            (0.8, 0.9, 'high'),
            (0.9, 1.0, 'very_high')
        ]
    
    def analyze_calibration(
        self,
        predictions: List[Any],
        ground_truth: List[Any],
        confidences: List[float],
        field_name: str
    ) -> Dict:
        """
        Analyze confidence calibration for a field.
        
        Args:
            predictions: List of predicted values
            ground_truth: List of ground truth values
            confidences: List of confidence scores
            field_name: Name of the field being analyzed
            
        Returns:
            Dictionary with calibration analysis
        """
        if not predictions or not ground_truth or not confidences:
            return self._empty_calibration_result()
        
        # Group predictions by confidence bucket
        bucket_data = {name: {'predictions': [], 'truth': [], 'confidences': []}
                      for _, _, name in self.confidence_buckets}
        
        for pred, truth, conf in zip(predictions, ground_truth, confidences):
            # Find bucket
            for min_conf, max_conf, bucket_name in self.confidence_buckets:
                if min_conf <= conf < max_conf or (max_conf == 1.0 and conf == 1.0):
                    bucket_data[bucket_name]['predictions'].append(pred)
                    bucket_data[bucket_name]['truth'].append(truth)
                    bucket_data[bucket_name]['confidences'].append(conf)
                    break
        
        # Calculate metrics for each bucket
        by_bucket = {}
        for min_conf, max_conf, bucket_name in self.confidence_buckets:
            bucket = bucket_data[bucket_name]
            
            if not bucket['predictions']:
                by_bucket[bucket_name] = {
                    'confidence_range': (min_conf, max_conf),
                    'count': 0,
                    'accuracy': 0.0,
                    'avg_confidence': 0.0
                }
                continue
            
            # Calculate accuracy for this bucket
            accuracy = MetricsCalculator.calculate_accuracy(
                bucket['predictions'],
                bucket['truth']
            )
            
            avg_confidence = np.mean(bucket['confidences'])
            
            by_bucket[bucket_name] = {
                'confidence_range': (min_conf, max_conf),
                'count': len(bucket['predictions']),
                'accuracy': accuracy,
                'avg_confidence': avg_confidence
            }
        
        # Calculate Expected Calibration Error (ECE)
        ece = self.calculate_ece(predictions, ground_truth, confidences)
        
        # Determine if well-calibrated (ECE < 0.1 is generally good)
        is_well_calibrated = ece < 0.1
        
        # Generate calibration plot data
        calibration_plot_data = [
            (bucket['avg_confidence'], bucket['accuracy'])
            for bucket in by_bucket.values()
            if bucket['count'] > 0
        ]
        
        return {
            'by_bucket': by_bucket,
            'expected_calibration_error': ece,
            'is_well_calibrated': is_well_calibrated,
            'calibration_plot_data': calibration_plot_data
        }
    
    def calculate_ece(
        self,
        predictions: List[Any],
        ground_truth: List[Any],
        confidences: List[float]
    ) -> float:
        """
        Calculate Expected Calibration Error (ECE).
        
        ECE measures the difference between confidence and accuracy.
        Lower is better (0 = perfectly calibrated).
        
        Args:
            predictions: List of predicted values
            ground_truth: List of ground truth values
            confidences: List of confidence scores
            
        Returns:
            ECE score [0, 1]
        """
        if not predictions or not ground_truth or not confidences:
            return 1.0
        
        # Group by confidence buckets
        bucket_errors = []
        total_samples = len(predictions)
        
        for min_conf, max_conf, _ in self.confidence_buckets:
            # Get samples in this bucket
            bucket_preds = []
            bucket_truth = []
            bucket_confs = []
            
            for pred, truth, conf in zip(predictions, ground_truth, confidences):
                if min_conf <= conf < max_conf or (max_conf == 1.0 and conf == 1.0):
                    bucket_preds.append(pred)
                    bucket_truth.append(truth)
                    bucket_confs.append(conf)
            
            if not bucket_preds:
                continue
            
            # Calculate accuracy and average confidence for bucket
            accuracy = MetricsCalculator.calculate_accuracy(bucket_preds, bucket_truth)
            avg_confidence = np.mean(bucket_confs)
            
            # Weight by bucket size
            weight = len(bucket_preds) / total_samples
            
            # Add weighted error
            bucket_errors.append(weight * abs(avg_confidence - accuracy))
        
        return sum(bucket_errors)
    
    def _empty_calibration_result(self) -> Dict:
        """Return empty calibration result."""
        return {
            'by_bucket': {},
            'expected_calibration_error': 1.0,
            'is_well_calibrated': False,
            'calibration_plot_data': []
        }


class DocumentEvaluator:
    """
    Evaluate document processing accuracy.
    
    Compares predictions against ground truth from SROIE dataset
    and provides comprehensive metrics.
    """
    
    def __init__(self, processor: DocumentProcessor):
        """
        Initialize evaluator.
        
        Args:
            processor: DocumentProcessor instance to evaluate
        """
        self.processor = processor
        self.metrics_calculator = MetricsCalculator()
        self.calibration_analyzer = ConfidenceCalibrationAnalyzer()
        
        logger.info("DocumentEvaluator initialized")
    
    def evaluate_dataset(
        self,
        split: str = 'train',
        limit: Optional[int] = None
    ) -> Dict:
        """
        Evaluate on SROIE dataset.
        
        Args:
            split: 'train' or 'test'
            limit: Max samples to evaluate (None = all)
            
        Returns:
            Comprehensive evaluation results
        """
        logger.info(f"Starting evaluation on {split} split (limit={limit})")
        start_time = time.time()
        
        # Load dataset using SROIEDataLoader
        data_loader = SROIEDataLoader(split=split)
        samples = data_loader.load_dataset()
        
        if limit:
            samples = samples[:limit]
        
        logger.info(f"Loaded {len(samples)} samples for evaluation")
        
        # Process all samples
        results = []
        for i, sample in enumerate(samples):
            if (i + 1) % 50 == 0:
                logger.info(f"Processing sample {i + 1}/{len(samples)}")
            
            try:
                # Process document
                result = self.processor.process_document(sample['image_path'])

                # Store result with ground truth
                results.append({
                    'image_path': sample['image_path'],
                    'image_id': sample.get('image_id'),
                    'prediction': {
                        'date': result['fields']['date']['value'],
                        'total': result['fields']['total']['value']
                    },
                    'confidence': {
                        'date': result['fields']['date']['confidence'],
                        'total': result['fields']['total']['confidence']
                    },
                    'ground_truth': sample['entities'],
                    'success': result['metadata']['success']
                })
            except Exception as e:
                logger.error(f"Failed to process {sample['image_path']}: {e}")
                results.append({
                    'image_path': sample['image_path'],
                    'image_id': sample.get('image_id'),
                    'prediction': {},
                    'confidence': {},
                    'ground_truth': sample['entities'],
                    'success': False
                })
        
        # Calculate metrics
        evaluation_results = self._calculate_metrics(results)
        evaluation_results['samples_evaluated'] = len(samples)
        evaluation_results['processing_time'] = time.time() - start_time
        
        logger.info(
            f"Evaluation complete: {len(samples)} samples in "
            f"{evaluation_results['processing_time']:.2f}s"
        )
        
        return evaluation_results

    def evaluate_with_error_tracking(
        self,
        split: str = 'train',
        limit: Optional[int] = None
    ) -> Tuple[Dict, List[Dict]]:
        """
        Evaluate dataset and return structured error tracking records.

        This method extends standard evaluation by collecting OCR text,
        field-level raw values, confidences, and per-field error records
        suitable for Phase 8 error analysis.

        Args:
            split: 'train' or 'test'
            limit: Max samples to evaluate (None = all)

        Returns:
            Tuple of:
                - evaluation_results: Standard evaluation metrics
                - error_records: List of field-level records with OCR context
        """
        logger.info(
            f"Starting evaluation with error tracking on {split} split "
            f"(limit={limit})"
        )
        start_time = time.time()

        data_loader = SROIEDataLoader(split=split)
        samples = data_loader.load_dataset()

        if limit:
            samples = samples[:limit]

        logger.info(f"Loaded {len(samples)} samples for tracked evaluation")

        results = []
        error_records = []

        for i, sample in enumerate(samples):
            if (i + 1) % 50 == 0:
                logger.info(f"Processing sample {i + 1}/{len(samples)}")

            try:
                result = self.processor.process_document(
                    sample['image_path'],
                    return_intermediate=True
                )

                prediction = {
                    'date': result['fields']['date']['value'],
                    'total': result['fields']['total']['value']
                }
                confidence = {
                    'date': result['fields']['date']['confidence'],
                    'total': result['fields']['total']['confidence']
                }
                raw_prediction = {
                    'date': result['fields']['date'].get('raw_value', ''),
                    'total': result['fields']['total'].get('raw_value', '')
                }
                ocr_text = (
                    result.get('intermediate', {})
                    .get('ocr_result', {})
                    .get('text', '')
                )

                results.append({
                    'image_path': sample['image_path'],
                    'image_id': sample.get('image_id'),
                    'prediction': prediction,
                    'confidence': confidence,
                    'raw_prediction': raw_prediction,
                    'ground_truth': sample['entities'],
                    'ocr_text': ocr_text,
                    'success': result['metadata']['success']
                })

            except Exception as e:
                logger.error(f"Failed to process {sample['image_path']}: {e}")
                results.append({
                    'image_path': sample['image_path'],
                    'image_id': sample.get('image_id'),
                    'prediction': {},
                    'confidence': {},
                    'raw_prediction': {},
                    'ground_truth': sample['entities'],
                    'ocr_text': '',
                    'success': False
                })

        evaluation_results = self._calculate_metrics(results)
        evaluation_results['samples_evaluated'] = len(samples)
        evaluation_results['processing_time'] = time.time() - start_time

        for result in results:
            for field in ['date', 'total']:
                pred = result['prediction'].get(field)
                truth = result['ground_truth'].get(field)
                conf = result['confidence'].get(field, 0.0)

                error_records.append({
                    'image_id': result.get('image_id'),
                    'image_path': result.get('image_path'),
                    'field_name': field,
                    'prediction': pred,
                    'ground_truth': truth,
                    'confidence': conf,
                    'raw_prediction': result.get('raw_prediction', {}).get(field, ''),
                    'ocr_text': result.get('ocr_text', ''),
                    'success': result.get('success', False),
                    'is_correct': self._values_match(pred, truth, field)
                })

        logger.info(
            f"Tracked evaluation complete: {len(samples)} samples, "
            f"{len(error_records)} field records"
        )

        return evaluation_results, error_records
    
    def _calculate_metrics(self, results: List[Dict]) -> Dict:
        """
        Calculate comprehensive metrics from results.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Dictionary with all metrics
        """
        # Extract predictions and ground truth for each field
        fields = ['date', 'total']
        field_data = {field: {'pred': [], 'truth': [], 'conf': []}
                     for field in fields}
        
        for result in results:
            for field in fields:
                pred = result['prediction'].get(field)
                truth = result['ground_truth'].get(field)
                conf = result['confidence'].get(field, 0.0)
                
                field_data[field]['pred'].append(pred)
                field_data[field]['truth'].append(truth)
                field_data[field]['conf'].append(conf)
        
        # Calculate per-field metrics
        per_field = {}
        confidence_analysis = {}
        
        for field in fields:
            per_field[field] = self.evaluate_field(
                field_data[field]['pred'],
                field_data[field]['truth'],
                field_data[field]['conf'],
                field
            )
            
            confidence_analysis[field] = self.calibration_analyzer.analyze_calibration(
                field_data[field]['pred'],
                field_data[field]['truth'],
                field_data[field]['conf'],
                field
            )
        
        # Calculate overall metrics
        all_preds = []
        all_truth = []
        for field in fields:
            all_preds.extend(field_data[field]['pred'])
            all_truth.extend(field_data[field]['truth'])
        
        overall_accuracy = self.metrics_calculator.calculate_accuracy(
            all_preds, all_truth
        )
        
        return {
            'overall': {
                'accuracy': overall_accuracy,
            },
            'per_field': per_field,
            'confidence_analysis': confidence_analysis
        }
    
    def evaluate_field(
        self,
        predictions: List[Any],
        ground_truth: List[Any],
        confidences: List[float],
        field_name: str
    ) -> Dict:
        """
        Evaluate a single field.
        
        Args:
            predictions: List of predicted values
            ground_truth: List of ground truth values
            confidences: List of confidence scores
            field_name: Name of the field
            
        Returns:
            Dictionary with field metrics
        """
        # Calculate basic metrics
        accuracy = self.metrics_calculator.calculate_accuracy(
            predictions, ground_truth
        )
        
        precision, recall, f1 = self.metrics_calculator.calculate_precision_recall_f1(
            predictions, ground_truth
        )
        
        # Calculate extraction rate (how often we extract something)
        extraction_rate = sum(
            1 for pred in predictions if pred is not None and pred != ''
        ) / len(predictions) if predictions else 0.0
        
        # Calculate fuzzy match for string fields
        fuzzy_match = 0.0
        if field_name in ['date', 'company', 'address']:
            str_preds = [str(p) if p is not None else '' for p in predictions]
            str_truth = [str(t) if t is not None else '' for t in ground_truth]
            fuzzy_match = self.metrics_calculator.calculate_fuzzy_match(
                str_preds, str_truth
            )
        
        # Calculate exact match (same as accuracy but more explicit)
        exact_match = accuracy
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'exact_match': exact_match,
            'fuzzy_match': fuzzy_match,
            'extraction_rate': extraction_rate
        }

    def _values_match(
        self,
        pred_value: Any,
        true_value: Any,
        field_name: str
    ) -> bool:
        """
        Check if predicted and true values match for a field.

        Uses strict normalized matching for dates and tolerance-based matching
        for totals to align tracked errors with evaluation behavior.
        """
        if pred_value is None or true_value is None:
            return False

        pred_str = str(pred_value).strip().lower()
        true_str = str(true_value).strip().lower()

        if field_name == 'total':
            try:
                pred_num = float(pred_str.replace('$', '').replace(',', ''))
                true_num = float(true_str.replace('$', '').replace(',', ''))
                return abs(pred_num - true_num) < 0.01
            except (ValueError, TypeError):
                return pred_str == true_str

        return pred_str == true_str


# Made with Bob