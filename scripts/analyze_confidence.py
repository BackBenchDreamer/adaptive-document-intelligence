#!/usr/bin/env python3
"""
Confidence Analysis Script

Analyze confidence scores on validation samples, generate calibration data,
and compare calibrated vs uncalibrated confidence scores.

Usage:
    python scripts/analyze_confidence.py --samples 100
    python scripts/analyze_confidence.py --calibrate --output calibration.json
    python scripts/analyze_confidence.py --compare
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import get_logger
from tests.data.sroie_loader import SROIEDataLoader
from pipeline.ocr import OCRManager
from pipeline.extractor import ExtractionManager
from pipeline.confidence import ConfidenceManager, ConfidenceCalibrator

logger = logging.getLogger(__name__)


class ConfidenceAnalyzer:
    """Analyze confidence scores on validation data."""
    
    def __init__(self, data_dir: str):
        """
        Initialize analyzer.
        
        Args:
            data_dir: Path to SROIE dataset
        """
        self.data_loader = SROIEDataLoader(split='train')
        self.ocr_engine = OCRManager(preferred_engine='paddleocr')
        self.extractor = ExtractionManager()
        self.confidence_mgr = ConfidenceManager(use_calibration=False)
        
        logger.info("Initialized ConfidenceAnalyzer")
    
    def analyze_samples(self, num_samples: int = 100) -> Dict:
        """
        Analyze confidence scores on validation samples.
        
        Args:
            num_samples: Number of samples to analyze
            
        Returns:
            Analysis results with statistics
        """
        logger.info(f"Analyzing {num_samples} samples...")
        
        # Load samples
        all_samples = self.data_loader.load_dataset()
        samples = [s for s in all_samples if s['has_required_fields']][:num_samples]
        
        # Convert to expected format
        samples = [{
            'image_path': Path(s['image_path']),
            'ground_truth': s['entities']
        } for s in samples]
        
        results = {
            'total_samples': len(samples),
            'fields': {
                'date': {'scores': [], 'correct': [], 'factors': []},
                'total': {'scores': [], 'correct': [], 'factors': []},
                'invoice_number': {'scores': [], 'correct': [], 'factors': []}
            },
            'timing': {
                'ocr_time': 0.0,
                'extraction_time': 0.0,
                'confidence_time': 0.0
            }
        }
        
        for i, sample in enumerate(samples):
            try:
                logger.info(f"Processing sample {i+1}/{len(samples)}: {sample['image_path'].name}")
                
                # Run OCR
                start_time = time.time()
                ocr_result = self.ocr_engine.extract_text(str(sample['image_path']))
                results['timing']['ocr_time'] += time.time() - start_time
                
                # Extract fields
                start_time = time.time()
                extraction_results = self.extractor.extract_fields(ocr_result)
                results['timing']['extraction_time'] += time.time() - start_time
                
                # Score confidence
                start_time = time.time()
                scored_results = self.confidence_mgr.score_extraction(
                    extraction_results,
                    ocr_result
                )
                results['timing']['confidence_time'] += time.time() - start_time
                
                # Analyze each field
                for field_name in ['date', 'total', 'invoice_number']:
                    if field_name in scored_results:
                        field_result = scored_results[field_name]
                        ground_truth = sample['ground_truth'].get(field_name)
                        
                        # Record confidence score
                        confidence = field_result['confidence']
                        results['fields'][field_name]['scores'].append(confidence)
                        
                        # Check if correct
                        is_correct = self._check_correctness(
                            field_result['value'],
                            ground_truth,
                            field_name
                        )
                        results['fields'][field_name]['correct'].append(is_correct)
                        
                        # Record factors
                        results['fields'][field_name]['factors'].append(
                            field_result['confidence_factors']
                        )
                        
                        logger.debug(
                            f"{field_name}: conf={confidence:.3f}, "
                            f"correct={is_correct}, value={field_result['value']}"
                        )
                
            except Exception as e:
                logger.error(f"Error processing sample {i+1}: {e}")
                continue
        
        # Calculate statistics
        results['statistics'] = self._calculate_statistics(results)
        
        return results
    
    def _check_correctness(self, pred_value, true_value, field_name: str) -> bool:
        """Check if prediction matches ground truth."""
        if pred_value is None or true_value is None:
            return False
        
        pred_str = str(pred_value).strip().lower()
        true_str = str(true_value).strip().lower()
        
        if field_name == 'total':
            # Allow small numerical differences
            try:
                pred_num = float(pred_str.replace('$', '').replace(',', ''))
                true_num = float(true_str.replace('$', '').replace(',', ''))
                return abs(pred_num - true_num) < 0.01
            except:
                return pred_str == true_str
        else:
            return pred_str == true_str
    
    def _calculate_statistics(self, results: Dict) -> Dict:
        """Calculate statistics from results."""
        stats = {}
        
        for field_name, field_data in results['fields'].items():
            scores = field_data['scores']
            correct = field_data['correct']
            
            if not scores:
                continue
            
            # Overall accuracy
            accuracy = sum(correct) / len(correct) if correct else 0.0
            
            # Confidence distribution
            avg_confidence = sum(scores) / len(scores)
            min_confidence = min(scores)
            max_confidence = max(scores)
            
            # Calibration analysis (confidence vs accuracy)
            bins = self._bin_confidence_accuracy(scores, correct)
            
            # Factor analysis
            factors = field_data['factors']
            avg_factors = self._average_factors(factors)
            
            stats[field_name] = {
                'accuracy': accuracy,
                'avg_confidence': avg_confidence,
                'min_confidence': min_confidence,
                'max_confidence': max_confidence,
                'calibration_bins': bins,
                'avg_factors': avg_factors,
                'num_samples': len(scores)
            }
        
        return stats
    
    def _bin_confidence_accuracy(
        self,
        scores: List[float],
        correct: List[bool],
        num_bins: int = 5
    ) -> List[Dict]:
        """Bin confidence scores and calculate accuracy per bin."""
        bins = []
        bin_size = 1.0 / num_bins
        
        for i in range(num_bins):
            bin_min = i * bin_size
            bin_max = (i + 1) * bin_size
            
            # Find samples in this bin
            bin_scores = []
            bin_correct = []
            
            for score, is_correct in zip(scores, correct):
                if bin_min <= score < bin_max or (i == num_bins - 1 and score == 1.0):
                    bin_scores.append(score)
                    bin_correct.append(is_correct)
            
            if bin_scores:
                bins.append({
                    'range': f'{bin_min:.2f}-{bin_max:.2f}',
                    'count': len(bin_scores),
                    'avg_confidence': sum(bin_scores) / len(bin_scores),
                    'accuracy': sum(bin_correct) / len(bin_correct)
                })
        
        return bins
    
    def _average_factors(self, factors: List[Dict]) -> Dict:
        """Calculate average factor values."""
        if not factors:
            return {}
        
        avg = {}
        factor_names = factors[0].keys()
        
        for name in factor_names:
            values = [f[name] for f in factors if name in f]
            avg[name] = sum(values) / len(values) if values else 0.0
        
        return avg
    
    def generate_calibration_data(
        self,
        num_samples: int = 100,
        output_file: Optional[str] = None
    ) -> Dict:
        """
        Generate calibration data from validation samples.
        
        Args:
            num_samples: Number of samples to use
            output_file: Optional file to save calibration data
            
        Returns:
            Calibration data
        """
        logger.info(f"Generating calibration data from {num_samples} samples...")
        
        # Analyze samples
        results = self.analyze_samples(num_samples)
        
        # Build calibration data
        calibration_data = {
            'metadata': {
                'num_samples': results['total_samples'],
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'fields': {}
        }
        
        for field_name, stats in results['statistics'].items():
            calibration_data['fields'][field_name] = {
                'accuracy': stats['accuracy'],
                'avg_confidence': stats['avg_confidence'],
                'calibration_bins': stats['calibration_bins']
            }
        
        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(calibration_data, f, indent=2)
            
            logger.info(f"Saved calibration data to {output_file}")
        
        return calibration_data
    
    def compare_calibration(self, num_samples: int = 50) -> Dict:
        """
        Compare calibrated vs uncalibrated confidence scores.
        
        Args:
            num_samples: Number of samples to compare
            
        Returns:
            Comparison results
        """
        logger.info(f"Comparing calibrated vs uncalibrated on {num_samples} samples...")
        
        # First, generate calibration data
        calibration_samples = min(100, num_samples * 2)
        all_samples = self.data_loader.load_dataset()
        valid_samples = [s for s in all_samples if s['has_required_fields']][:calibration_samples]
        
        # Convert to expected format
        valid_samples = [{
            'image_path': Path(s['image_path']),
            'ground_truth': s['entities']
        } for s in valid_samples]
        
        # Split into calibration and test sets
        calib_samples = valid_samples[:calibration_samples // 2]
        test_samples = valid_samples[calibration_samples // 2:calibration_samples // 2 + num_samples]
        
        # Build calibration data
        logger.info("Building calibration data...")
        predictions = []
        ground_truth = []
        
        for sample in calib_samples:
            try:
                ocr_result = self.ocr_engine.extract_text(str(sample['image_path']))
                extraction_results = self.extractor.extract_fields(ocr_result)
                scored_results = self.confidence_mgr.score_extraction(
                    extraction_results,
                    ocr_result
                )
                
                predictions.append(scored_results)
                ground_truth.append(sample['ground_truth'])
            except Exception as e:
                logger.error(f"Error in calibration: {e}")
                continue
        
        # Fit calibrator
        calibrator = ConfidenceCalibrator()
        calibrator.fit(predictions, ground_truth)
        
        # Test both versions
        logger.info("Testing uncalibrated vs calibrated...")
        uncalibrated_mgr = ConfidenceManager(use_calibration=False)
        calibrated_mgr = ConfidenceManager(use_calibration=True, calibrator=calibrator)
        
        comparison = {
            'uncalibrated': {'date': [], 'total': [], 'invoice_number': []},
            'calibrated': {'date': [], 'total': [], 'invoice_number': []},
            'ground_truth': {'date': [], 'total': [], 'invoice_number': []}
        }
        
        for sample in test_samples:
            try:
                ocr_result = self.ocr_engine.extract_text(str(sample['image_path']))
                extraction_results = self.extractor.extract_fields(ocr_result)
                
                # Uncalibrated
                uncalib_results = uncalibrated_mgr.score_extraction(
                    extraction_results,
                    ocr_result
                )
                
                # Calibrated
                calib_results = calibrated_mgr.score_extraction(
                    extraction_results,
                    ocr_result
                )
                
                # Record results
                for field_name in ['date', 'total', 'invoice_number']:
                    if field_name in uncalib_results:
                        comparison['uncalibrated'][field_name].append(
                            uncalib_results[field_name]['confidence']
                        )
                        comparison['calibrated'][field_name].append(
                            calib_results[field_name]['confidence']
                        )
                        
                        is_correct = self._check_correctness(
                            uncalib_results[field_name]['value'],
                            sample['ground_truth'].get(field_name),
                            field_name
                        )
                        comparison['ground_truth'][field_name].append(is_correct)
                
            except Exception as e:
                logger.error(f"Error in comparison: {e}")
                continue
        
        # Calculate comparison statistics
        comparison['statistics'] = self._calculate_comparison_stats(comparison)
        
        return comparison
    
    def _calculate_comparison_stats(self, comparison: Dict) -> Dict:
        """Calculate comparison statistics."""
        stats = {}
        
        for field_name in ['date', 'total', 'invoice_number']:
            uncalib = comparison['uncalibrated'][field_name]
            calib = comparison['calibrated'][field_name]
            correct = comparison['ground_truth'][field_name]
            
            if not uncalib:
                continue
            
            # Calculate calibration error (difference between confidence and accuracy)
            uncalib_bins = self._bin_confidence_accuracy(uncalib, correct)
            calib_bins = self._bin_confidence_accuracy(calib, correct)
            
            # Calculate expected calibration error (ECE)
            uncalib_ece = self._calculate_ece(uncalib_bins)
            calib_ece = self._calculate_ece(calib_bins)
            
            stats[field_name] = {
                'uncalibrated': {
                    'avg_confidence': sum(uncalib) / len(uncalib),
                    'ece': uncalib_ece,
                    'bins': uncalib_bins
                },
                'calibrated': {
                    'avg_confidence': sum(calib) / len(calib),
                    'ece': calib_ece,
                    'bins': calib_bins
                },
                'accuracy': sum(correct) / len(correct),
                'improvement': uncalib_ece - calib_ece
            }
        
        return stats
    
    def _calculate_ece(self, bins: List[Dict]) -> float:
        """Calculate Expected Calibration Error."""
        total_samples = sum(b['count'] for b in bins)
        if total_samples == 0:
            return 0.0
        
        ece = 0.0
        for bin_data in bins:
            weight = bin_data['count'] / total_samples
            error = abs(bin_data['avg_confidence'] - bin_data['accuracy'])
            ece += weight * error
        
        return ece


def print_analysis_results(results: Dict):
    """Print analysis results in a readable format."""
    print("\n" + "="*80)
    print("CONFIDENCE ANALYSIS RESULTS")
    print("="*80)
    
    print(f"\nTotal Samples: {results['total_samples']}")
    print(f"\nTiming:")
    print(f"  OCR Time: {results['timing']['ocr_time']:.2f}s")
    print(f"  Extraction Time: {results['timing']['extraction_time']:.2f}s")
    print(f"  Confidence Time: {results['timing']['confidence_time']:.2f}s")
    
    print("\n" + "-"*80)
    print("FIELD STATISTICS")
    print("-"*80)
    
    for field_name, stats in results['statistics'].items():
        print(f"\n{field_name.upper()}:")
        print(f"  Accuracy: {stats['accuracy']:.2%}")
        print(f"  Avg Confidence: {stats['avg_confidence']:.3f}")
        print(f"  Confidence Range: [{stats['min_confidence']:.3f}, {stats['max_confidence']:.3f}]")
        print(f"  Samples: {stats['num_samples']}")
        
        print(f"\n  Average Factors:")
        for factor, value in stats['avg_factors'].items():
            print(f"    {factor}: {value:.3f}")
        
        print(f"\n  Calibration Bins:")
        print(f"    {'Range':<15} {'Count':<8} {'Avg Conf':<12} {'Accuracy':<10}")
        for bin_data in stats['calibration_bins']:
            print(
                f"    {bin_data['range']:<15} "
                f"{bin_data['count']:<8} "
                f"{bin_data['avg_confidence']:<12.3f} "
                f"{bin_data['accuracy']:<10.2%}"
            )


def print_comparison_results(comparison: Dict):
    """Print comparison results."""
    print("\n" + "="*80)
    print("CALIBRATION COMPARISON RESULTS")
    print("="*80)
    
    for field_name, stats in comparison['statistics'].items():
        print(f"\n{field_name.upper()}:")
        print(f"  Accuracy: {stats['accuracy']:.2%}")
        
        print(f"\n  Uncalibrated:")
        print(f"    Avg Confidence: {stats['uncalibrated']['avg_confidence']:.3f}")
        print(f"    ECE: {stats['uncalibrated']['ece']:.4f}")
        
        print(f"\n  Calibrated:")
        print(f"    Avg Confidence: {stats['calibrated']['avg_confidence']:.3f}")
        print(f"    ECE: {stats['calibrated']['ece']:.4f}")
        
        print(f"\n  Improvement: {stats['improvement']:.4f} (lower ECE is better)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze confidence scores on validation data'
    )
    parser.add_argument(
        '--data-dir',
        default='tests/SROIE2019',
        help='Path to SROIE dataset'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=50,
        help='Number of samples to analyze'
    )
    parser.add_argument(
        '--calibrate',
        action='store_true',
        help='Generate calibration data'
    )
    parser.add_argument(
        '--output',
        help='Output file for calibration data'
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare calibrated vs uncalibrated'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    import logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = get_logger(__name__)
    
    # Create analyzer
    analyzer = ConfidenceAnalyzer(args.data_dir)
    
    try:
        if args.compare:
            # Compare calibrated vs uncalibrated
            comparison = analyzer.compare_calibration(args.samples)
            print_comparison_results(comparison)
            
        elif args.calibrate:
            # Generate calibration data
            calibration_data = analyzer.generate_calibration_data(
                args.samples,
                args.output
            )
            print(f"\nGenerated calibration data for {calibration_data['metadata']['num_samples']} samples")
            
            if args.output:
                print(f"Saved to: {args.output}")
            else:
                print(json.dumps(calibration_data, indent=2))
        
        else:
            # Analyze confidence scores
            results = analyzer.analyze_samples(args.samples)
            print_analysis_results(results)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

# Made with Bob
