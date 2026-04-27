"""
Confidence Scoring Module

This module provides confidence scoring for extracted fields by combining
multiple quality factors including extraction confidence, OCR quality,
value validity, and pattern strength.

Author: Adaptive Document Intelligence System
Phase: 5 - Confidence Scoring
"""

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import time

logger = logging.getLogger(__name__)


class ConfidenceScorer(ABC):
    """
    Abstract base class for confidence scoring.
    
    Combines multiple quality factors into a final confidence score.
    """
    
    @abstractmethod
    def calculate_confidence(
        self,
        extraction_result: Dict,
        ocr_result: Dict,
        field_name: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate calibrated confidence score.
        
        Args:
            extraction_result: Output from field extractor
            ocr_result: Output from OCR module
            field_name: 'date', 'total', or 'invoice_number'
            
        Returns:
            Tuple of (confidence score [0, 1], factor breakdown dict)
        """
        pass


class MultiFactorConfidenceScorer(ConfidenceScorer):
    """
    Calculate confidence using multiple quality factors.
    
    Factors:
    1. Extraction confidence (from heuristics) - 40%
    2. OCR quality score - 30%
    3. Value validity (format, range checks) - 20%
    4. Pattern strength (how well it matches expected patterns) - 10%
    
    Formula:
    confidence = (
        extraction_conf * 0.4 +
        ocr_quality * 0.3 +
        validity_score * 0.2 +
        pattern_strength * 0.1
    )
    """
    
    def __init__(self):
        """Initialize scorer with calibration parameters."""
        self.weights = {
            'extraction': 0.4,
            'ocr_quality': 0.3,
            'validity': 0.2,
            'pattern': 0.1
        }
        logger.info(f"Initialized MultiFactorConfidenceScorer with weights: {self.weights}")
    
    def calculate_confidence(
        self,
        extraction_result: Dict,
        ocr_result: Dict,
        field_name: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate multi-factor confidence.
        
        Args:
            extraction_result: Dict with 'value', 'confidence', 'raw_value'
            ocr_result: Dict with OCR metadata
            field_name: Field type
            
        Returns:
            Tuple of (final_confidence, factor_breakdown)
        """
        try:
            # Extract base confidence from extraction result
            extraction_conf = extraction_result.get('confidence', 0.5)
            
            # Calculate individual factors
            ocr_quality = self._calculate_ocr_quality(ocr_result)
            validity_score = self._calculate_validity_score(
                extraction_result.get('value'),
                field_name
            )
            pattern_strength = self._calculate_pattern_strength(
                extraction_result.get('value'),
                extraction_result.get('raw_value', ''),
                field_name
            )
            
            # Combine factors with weights
            final_confidence = (
                extraction_conf * self.weights['extraction'] +
                ocr_quality * self.weights['ocr_quality'] +
                validity_score * self.weights['validity'] +
                pattern_strength * self.weights['pattern']
            )
            
            # Ensure confidence is in [0, 1]
            final_confidence = max(0.0, min(1.0, final_confidence))
            
            factor_breakdown = {
                'extraction': extraction_conf,
                'ocr_quality': ocr_quality,
                'validity': validity_score,
                'pattern': pattern_strength
            }
            
            logger.debug(
                f"Confidence for {field_name}: {final_confidence:.3f} "
                f"(factors: {factor_breakdown})"
            )
            
            return final_confidence, factor_breakdown
            
        except Exception as e:
            logger.error(f"Error calculating confidence for {field_name}: {e}")
            return 0.0, {
                'extraction': 0.0,
                'ocr_quality': 0.0,
                'validity': 0.0,
                'pattern': 0.0
            }
    
    def _calculate_ocr_quality(self, ocr_result: Dict) -> float:
        """
        Calculate OCR quality score.
        
        Factors:
        - OCR engine confidence (if available)
        - Text density (chars per area)
        - Text length (longer = more reliable)
        
        Returns:
            Score in [0, 1]
        """
        try:
            # Base confidence from OCR engine
            base_confidence = ocr_result.get('confidence', 0.5)
            
            # Text length factor (longer text generally means better OCR)
            text = ocr_result.get('text', '')
            text_length = len(text)
            length_factor = min(1.0, text_length / 500)
            
            # Combine factors
            quality = base_confidence * 0.7 + length_factor * 0.3
            
            return max(0.0, min(1.0, quality))
            
        except Exception as e:
            logger.warning(f"Error calculating OCR quality: {e}")
            return 0.5
    
    def _calculate_validity_score(
        self,
        value: Any,
        field_name: str
    ) -> float:
        """
        Calculate value validity score.
        
        Checks:
        - Date: Valid date, reasonable year (1900-2100)
        - Total: Positive, reasonable range ($0.01-$100,000)
        - Invoice: Reasonable length, format
        
        Returns:
            Score in [0, 1]
        """
        try:
            if value is None:
                return 0.0
            
            if field_name == 'date':
                return self._validate_date(value)
            elif field_name == 'total':
                return self._validate_total(value)
            elif field_name == 'invoice_number':
                return self._validate_invoice_number(value)
            else:
                logger.warning(f"Unknown field type: {field_name}")
                return 0.5
                
        except Exception as e:
            logger.warning(f"Error validating {field_name}: {e}")
            return 0.0
    
    def _validate_date(self, date_value: Any) -> float:
        """
        Validate date value.
        
        Checks:
        - Valid date format
        - Reasonable year (1900-2100)
        - Not too far in future (with tolerance)
        
        Returns:
            Validity score [0, 1]
        """
        try:
            # Handle string dates
            if isinstance(date_value, str):
                date_obj = datetime.fromisoformat(date_value)
            elif isinstance(date_value, datetime):
                date_obj = date_value
            else:
                return 0.0
            
            # Check year range
            if not (1900 <= date_obj.year <= 2100):
                return 0.3  # Invalid year
            
            # Check not too far in future (allow up to 1 year ahead)
            max_future = datetime.now() + timedelta(days=365)
            if date_obj <= max_future:
                return 1.0
            
            return 0.7  # Future date, but valid format
            
        except Exception as e:
            logger.debug(f"Date validation failed: {e}")
            return 0.0
    
    def _validate_total(self, amount: Any) -> float:
        """
        Validate total amount.
        
        Checks:
        - Positive value
        - Reasonable range ($0.01 - $100,000)
        - Not suspiciously round (e.g., exactly $1000.00)
        
        Returns:
            Validity score [0, 1]
        """
        try:
            # Convert to float if needed
            if isinstance(amount, str):
                amount = float(amount.replace('$', '').replace(',', ''))
            elif not isinstance(amount, (int, float)):
                return 0.0
            
            amount = float(amount)
            
            # Must be positive
            if amount <= 0:
                return 0.0
            
            # Check reasonable range
            if 0.01 <= amount <= 100000:
                # Penalize suspiciously round numbers
                if amount == round(amount) and amount >= 100:
                    return 0.8  # Might be subtotal or estimate
                return 1.0
            
            # Unusually high but possible
            if amount > 100000:
                return 0.5
            
            # Too small
            return 0.3
            
        except Exception as e:
            logger.debug(f"Total validation failed: {e}")
            return 0.0
    
    def _validate_invoice_number(self, invoice_num: Any) -> float:
        """
        Validate invoice number.
        
        Checks:
        - Reasonable length (3-30 chars)
        - Contains alphanumeric characters
        - Not all spaces or special chars
        
        Returns:
            Validity score [0, 1]
        """
        try:
            if not isinstance(invoice_num, str):
                invoice_num = str(invoice_num)
            
            # Remove whitespace
            invoice_num = invoice_num.strip()
            
            # Check length
            if not (3 <= len(invoice_num) <= 30):
                return 0.3
            
            # Must contain at least some alphanumeric
            if not re.search(r'[a-zA-Z0-9]', invoice_num):
                return 0.0
            
            # Check if it's mostly alphanumeric
            alnum_ratio = sum(c.isalnum() for c in invoice_num) / len(invoice_num)
            if alnum_ratio >= 0.5:
                return 1.0
            elif alnum_ratio >= 0.3:
                return 0.7
            else:
                return 0.4
                
        except Exception as e:
            logger.debug(f"Invoice number validation failed: {e}")
            return 0.0
    
    def _calculate_pattern_strength(
        self,
        value: Any,
        raw_value: str,
        field_name: str
    ) -> float:
        """
        Calculate pattern match strength.
        
        Checks:
        - Date: Common format (DD/MM/YYYY gets higher score)
        - Total: Proper currency format
        - Invoice: Standard patterns (INV-XXX, #XXX)
        
        Returns:
            Score in [0, 1]
        """
        try:
            if field_name == 'date':
                return self._check_date_pattern(raw_value)
            elif field_name == 'total':
                return self._check_total_pattern(raw_value)
            elif field_name == 'invoice_number':
                return self._check_invoice_pattern(raw_value)
            else:
                return 0.5
                
        except Exception as e:
            logger.warning(f"Error checking pattern for {field_name}: {e}")
            return 0.5
    
    def _check_date_pattern(self, raw_value: str) -> float:
        """Check date pattern strength."""
        if not raw_value:
            return 0.5
        
        # Common date patterns (higher score for more standard formats)
        patterns = [
            (r'\d{2}/\d{2}/\d{4}', 1.0),      # DD/MM/YYYY or MM/DD/YYYY
            (r'\d{4}-\d{2}-\d{2}', 0.95),     # YYYY-MM-DD (ISO)
            (r'\d{2}-\d{2}-\d{4}', 0.9),      # DD-MM-YYYY
            (r'\d{1,2}/\d{1,2}/\d{4}', 0.85), # D/M/YYYY
            (r'\d{2}\.\d{2}\.\d{4}', 0.8),    # DD.MM.YYYY
        ]
        
        for pattern, score in patterns:
            if re.search(pattern, raw_value):
                return score
        
        return 0.6  # Has some date-like structure
    
    def _check_total_pattern(self, raw_value: str) -> float:
        """Check total amount pattern strength."""
        if not raw_value:
            return 0.5
        
        # Currency patterns
        patterns = [
            (r'\$\s*\d+\.\d{2}', 1.0),        # $XX.XX
            (r'\d+\.\d{2}', 0.9),             # XX.XX
            (r'\$\s*\d+,\d{3}\.\d{2}', 0.95), # $X,XXX.XX
            (r'\d+,\d{3}\.\d{2}', 0.85),      # X,XXX.XX
        ]
        
        for pattern, score in patterns:
            if re.search(pattern, raw_value):
                return score
        
        # Has digits and decimal
        if re.search(r'\d+\.\d+', raw_value):
            return 0.7
        
        return 0.5
    
    def _check_invoice_pattern(self, raw_value: str) -> float:
        """Check invoice number pattern strength."""
        if not raw_value:
            return 0.5
        
        # Common invoice patterns
        patterns = [
            (r'INV[-\s]?\d+', 1.0),           # INV-XXX
            (r'#\d+', 0.95),                  # #XXX
            (r'[A-Z]{2,4}[-\s]?\d+', 0.9),    # ABC-XXX
            (r'\d{6,}', 0.85),                # Long number
        ]
        
        for pattern, score in patterns:
            if re.search(pattern, raw_value, re.IGNORECASE):
                return score
        
        # Has alphanumeric mix
        if re.search(r'[A-Za-z]', raw_value) and re.search(r'\d', raw_value):
            return 0.7
        
        return 0.6


class ConfidenceCalibrator:
    """
    Calibrate confidence scores based on validation data.
    
    Uses simple binning to map raw scores to calibrated probabilities.
    
    Example:
    - Raw score 0.8 → Calibrated 0.65 (actual accuracy)
    - Raw score 0.9 → Calibrated 0.85
    """
    
    def __init__(self):
        """Initialize calibrator."""
        self.calibration_data = {
            'date': [],
            'total': [],
            'invoice_number': []
        }
        self.calibration_bins = {
            'date': self._get_default_bins('date'),
            'total': self._get_default_bins('total'),
            'invoice_number': self._get_default_bins('invoice_number')
        }
        self.is_fitted = False
        logger.info("Initialized ConfidenceCalibrator with default bins")
    
    def _get_default_bins(self, field_name: str) -> List[Tuple[float, float]]:
        """
        Get default calibration bins for a field.
        
        These are conservative estimates that can be refined with validation data.
        """
        if field_name == 'date':
            return [
                (0.0, 0.0),   # 0.0-0.3 → 0% accuracy
                (0.3, 0.4),   # 0.3-0.5 → 40% accuracy
                (0.5, 0.6),   # 0.5-0.7 → 60% accuracy
                (0.7, 0.75),  # 0.7-0.8 → 75% accuracy
                (0.8, 0.85),  # 0.8-0.9 → 85% accuracy
                (0.9, 0.92),  # 0.9-1.0 → 92% accuracy
            ]
        elif field_name == 'total':
            return [
                (0.0, 0.0),   # 0.0-0.3 → 0% accuracy
                (0.3, 0.35),  # 0.3-0.5 → 35% accuracy
                (0.5, 0.55),  # 0.5-0.7 → 55% accuracy
                (0.7, 0.70),  # 0.7-0.8 → 70% accuracy
                (0.8, 0.80),  # 0.8-0.9 → 80% accuracy
                (0.9, 0.88),  # 0.9-1.0 → 88% accuracy
            ]
        else:  # invoice_number
            return [
                (0.0, 0.0),   # 0.0-0.3 → 0% accuracy
                (0.3, 0.30),  # 0.3-0.5 → 30% accuracy
                (0.5, 0.50),  # 0.5-0.7 → 50% accuracy
                (0.7, 0.65),  # 0.7-0.8 → 65% accuracy
                (0.8, 0.75),  # 0.8-0.9 → 75% accuracy
                (0.9, 0.85),  # 0.9-1.0 → 85% accuracy
            ]
    
    def fit(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict]
    ):
        """
        Fit calibrator using validation data.
        
        Args:
            predictions: List of extraction results with confidence scores
            ground_truth: List of ground truth values
        """
        try:
            logger.info(f"Fitting calibrator with {len(predictions)} samples")
            
            # Collect data for each field
            for field_name in ['date', 'total', 'invoice_number']:
                field_data = []
                
                for pred, gt in zip(predictions, ground_truth):
                    if field_name in pred and field_name in gt:
                        raw_conf = pred[field_name].get('confidence', 0.0)
                        pred_value = pred[field_name].get('value')
                        true_value = gt.get(field_name)
                        
                        # Check if prediction is correct
                        is_correct = self._values_match(pred_value, true_value, field_name)
                        
                        field_data.append((raw_conf, is_correct))
                
                self.calibration_data[field_name] = field_data
                
                # Update bins based on data
                if len(field_data) >= 10:
                    self.calibration_bins[field_name] = self._compute_bins(field_data)
            
            self.is_fitted = True
            logger.info("Calibrator fitted successfully")
            
        except Exception as e:
            logger.error(f"Error fitting calibrator: {e}")
            self.is_fitted = False
    
    def _values_match(self, pred_value: Any, true_value: Any, field_name: str) -> bool:
        """Check if predicted and true values match."""
        if pred_value is None or true_value is None:
            return False
        
        # Convert to strings for comparison
        pred_str = str(pred_value).strip().lower()
        true_str = str(true_value).strip().lower()
        
        if field_name == 'total':
            # For totals, allow small numerical differences
            try:
                pred_num = float(pred_str.replace('$', '').replace(',', ''))
                true_num = float(true_str.replace('$', '').replace(',', ''))
                return abs(pred_num - true_num) < 0.01
            except:
                return pred_str == true_str
        else:
            return pred_str == true_str
    
    def _compute_bins(self, field_data: List[Tuple[float, bool]]) -> List[Tuple[float, float]]:
        """
        Compute calibration bins from field data.
        
        Args:
            field_data: List of (confidence, is_correct) tuples
            
        Returns:
            List of (threshold, calibrated_value) tuples
        """
        # Sort by confidence
        sorted_data = sorted(field_data, key=lambda x: x[0])
        
        # Create bins
        bins = []
        bin_size = len(sorted_data) // 6  # 6 bins
        
        for i in range(0, len(sorted_data), bin_size):
            bin_data = sorted_data[i:i+bin_size]
            if not bin_data:
                continue
            
            # Calculate accuracy in this bin
            accuracy = sum(1 for _, correct in bin_data if correct) / len(bin_data)
            threshold = bin_data[0][0]  # Min confidence in bin
            
            bins.append((threshold, accuracy))
        
        return bins if bins else self._get_default_bins('date')
    
    def calibrate(
        self,
        raw_confidence: float,
        field_name: str
    ) -> float:
        """
        Calibrate a raw confidence score.
        
        Args:
            raw_confidence: Uncalibrated score [0, 1]
            field_name: Field type
            
        Returns:
            Calibrated confidence [0, 1]
        """
        try:
            bins = self.calibration_bins.get(field_name, [])
            if not bins:
                return raw_confidence
            
            return self._bin_confidence(raw_confidence, bins)
            
        except Exception as e:
            logger.warning(f"Error calibrating confidence: {e}")
            return raw_confidence
    
    def _bin_confidence(
        self,
        raw_confidence: float,
        bins: List[Tuple[float, float]]
    ) -> float:
        """
        Map confidence to calibrated value using bins.
        
        Bins format: [(threshold, calibrated_value), ...]
        """
        # Find appropriate bin
        for i, (threshold, calibrated) in enumerate(bins):
            if i == len(bins) - 1:
                # Last bin
                return calibrated
            
            next_threshold = bins[i + 1][0]
            if threshold <= raw_confidence < next_threshold:
                # Interpolate between bins
                next_calibrated = bins[i + 1][1]
                ratio = (raw_confidence - threshold) / (next_threshold - threshold)
                return calibrated + ratio * (next_calibrated - calibrated)
        
        # Default to last bin
        return bins[-1][1] if bins else raw_confidence


class ConfidenceManager:
    """
    Manages confidence scoring for all fields.
    
    Coordinates multi-factor scoring and calibration.
    """
    
    def __init__(
        self,
        use_calibration: bool = False,
        calibrator: Optional[ConfidenceCalibrator] = None
    ):
        """
        Initialize confidence manager.
        
        Args:
            use_calibration: Whether to apply calibration
            calibrator: Pre-trained calibrator (optional)
        """
        self.scorer = MultiFactorConfidenceScorer()
        self.use_calibration = use_calibration
        self.calibrator = calibrator or ConfidenceCalibrator()
        
        logger.info(
            f"Initialized ConfidenceManager "
            f"(calibration={'enabled' if use_calibration else 'disabled'})"
        )
    
    def score_extraction(
        self,
        extraction_results: Dict,
        ocr_result: Dict
    ) -> Dict:
        """
        Score all extracted fields.
        
        Args:
            extraction_results: Output from ExtractionManager
            ocr_result: Output from OCR module
            
        Returns:
            {
                'date': {
                    'value': ...,
                    'confidence': float,  # Calibrated
                    'raw_confidence': float,
                    'confidence_factors': {
                        'extraction': float,
                        'ocr_quality': float,
                        'validity': float,
                        'pattern': float
                    }
                },
                'total': {...},
                'invoice_number': {...},
                'metadata': {
                    'calibration_applied': bool,
                    'scoring_time': float
                }
            }
        """
        start_time = time.time()
        
        try:
            scored_results = {}
            
            # Score each field
            for field_name in ['date', 'total', 'invoice_number']:
                if field_name in extraction_results:
                    extraction_result = extraction_results[field_name]
                    
                    # Calculate multi-factor confidence
                    raw_confidence, factors = self.scorer.calculate_confidence(
                        extraction_result,
                        ocr_result,
                        field_name
                    )
                    
                    # Apply calibration if enabled
                    if self.use_calibration and self.calibrator.is_fitted:
                        calibrated_confidence = self.calibrator.calibrate(
                            raw_confidence,
                            field_name
                        )
                    else:
                        calibrated_confidence = raw_confidence
                    
                    # Build result
                    scored_results[field_name] = {
                        'value': extraction_result.get('value'),
                        'confidence': calibrated_confidence,
                        'raw_confidence': raw_confidence,
                        'confidence_factors': factors
                    }
                    
                    logger.debug(
                        f"Scored {field_name}: "
                        f"raw={raw_confidence:.3f}, "
                        f"calibrated={calibrated_confidence:.3f}"
                    )
            
            # Add metadata
            scoring_time = time.time() - start_time
            scored_results['metadata'] = {
                'calibration_applied': self.use_calibration and self.calibrator.is_fitted,
                'scoring_time': scoring_time
            }
            
            logger.info(f"Scored {len(scored_results)-1} fields in {scoring_time:.3f}s")
            
            return scored_results
            
        except Exception as e:
            logger.error(f"Error scoring extraction: {e}")
            return {
                'metadata': {
                    'calibration_applied': False,
                    'scoring_time': time.time() - start_time,
                    'error': str(e)
                }
            }

# Made with Bob
