#!/usr/bin/env python3
"""
Evaluation Script for Adaptive Document Intelligence System.

This script runs comprehensive evaluation on the SROIE dataset and
provides detailed accuracy metrics and confidence calibration analysis.

Usage:
    # Evaluate on full training set
    python scripts/run_evaluation.py --split train
    
    # Evaluate on subset
    python scripts/run_evaluation.py --split train --limit 100
    
    # With detailed output
    python scripts/run_evaluation.py --split train --verbose --output results.json
    
    # Show confidence calibration
    python scripts/run_evaluation.py --split train --show-calibration
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import Config
from core.logging_config import get_logger
from pipeline.pipeline import DocumentProcessor
from tests.metrics.evaluation import DocumentEvaluator

logger = get_logger(__name__)


def print_separator(char='=', length=80):
    """Print a separator line."""
    print(char * length)


def print_section_header(title: str):
    """Print a section header."""
    print_separator()
    print(f"  {title}")
    print_separator()


def format_percentage(value: float) -> str:
    """Format a float as percentage."""
    return f"{value * 100:.2f}%"


def print_overall_metrics(results: dict):
    """Print overall evaluation metrics."""
    print_section_header("OVERALL METRICS")
    
    overall = results['overall']
    print(f"Samples Evaluated: {results['samples_evaluated']}")
    print(f"Processing Time:   {results['processing_time']:.2f}s")
    print(f"Avg Time/Sample:   {results['processing_time'] / results['samples_evaluated']:.3f}s")
    print(f"Overall Accuracy:  {format_percentage(overall['accuracy'])}")
    print()


def print_field_metrics(results: dict, verbose: bool = False):
    """Print per-field metrics."""
    print_section_header("PER-FIELD METRICS")
    
    per_field = results['per_field']
    
    for field_name, metrics in per_field.items():
        print(f"\n{field_name.upper()}:")
        print(f"  Accuracy:        {format_percentage(metrics['accuracy'])}")
        print(f"  Precision:       {format_percentage(metrics['precision'])}")
        print(f"  Recall:          {format_percentage(metrics['recall'])}")
        print(f"  F1 Score:        {format_percentage(metrics['f1'])}")
        print(f"  Extraction Rate: {format_percentage(metrics['extraction_rate'])}")
        
        if verbose:
            print(f"  Exact Match:     {format_percentage(metrics['exact_match'])}")
            print(f"  Fuzzy Match:     {format_percentage(metrics['fuzzy_match'])}")
    
    print()


def print_confidence_calibration(results: dict, show_buckets: bool = True):
    """Print confidence calibration analysis."""
    print_section_header("CONFIDENCE CALIBRATION ANALYSIS")
    
    confidence_analysis = results['confidence_analysis']
    
    for field_name, analysis in confidence_analysis.items():
        print(f"\n{field_name.upper()}:")
        print(f"  Expected Calibration Error (ECE): {analysis['expected_calibration_error']:.4f}")
        print(f"  Well Calibrated: {'✓ Yes' if analysis['is_well_calibrated'] else '✗ No'}")
        
        if show_buckets and analysis['by_bucket']:
            print(f"\n  Confidence Buckets:")
            print(f"  {'Bucket':<15} {'Range':<15} {'Count':<8} {'Accuracy':<12} {'Avg Conf':<12}")
            print(f"  {'-'*15} {'-'*15} {'-'*8} {'-'*12} {'-'*12}")
            
            for bucket_name, bucket_data in analysis['by_bucket'].items():
                if bucket_data['count'] > 0:
                    range_str = f"{bucket_data['confidence_range'][0]:.1f}-{bucket_data['confidence_range'][1]:.1f}"
                    accuracy_str = format_percentage(bucket_data['accuracy'])
                    conf_str = f"{bucket_data['avg_confidence']:.3f}"
                    
                    print(f"  {bucket_name:<15} {range_str:<15} {bucket_data['count']:<8} {accuracy_str:<12} {conf_str:<12}")
    
    print()


def print_calibration_interpretation(results: dict):
    """Print interpretation of calibration results."""
    print_section_header("CALIBRATION INTERPRETATION")
    
    confidence_analysis = results['confidence_analysis']
    
    for field_name, analysis in confidence_analysis.items():
        ece = analysis['expected_calibration_error']
        is_calibrated = analysis['is_well_calibrated']
        
        print(f"\n{field_name.upper()}:")
        
        if is_calibrated:
            print(f"  ✓ Confidence scores are well-calibrated (ECE={ece:.4f})")
            print(f"    High confidence predictions are reliably accurate.")
        else:
            print(f"  ✗ Confidence scores need calibration (ECE={ece:.4f})")
            
            if ece > 0.2:
                print(f"    WARNING: Large calibration error detected!")
                print(f"    Confidence scores may not reflect actual accuracy.")
            else:
                print(f"    Moderate calibration error. Consider confidence adjustment.")
        
        # Check if high confidence predictions are actually accurate
        by_bucket = analysis['by_bucket']
        if 'very_high' in by_bucket and by_bucket['very_high']['count'] > 0:
            high_conf_accuracy = by_bucket['very_high']['accuracy']
            if high_conf_accuracy < 0.9:
                print(f"    ⚠ High confidence predictions (0.9-1.0) only {format_percentage(high_conf_accuracy)} accurate")
                print(f"      System is overconfident!")
    
    print()


def save_results(results: dict, output_path: str):
    """Save results to JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        print(f"\n✗ Failed to save results: {e}")


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(
        description='Evaluate document processing system on SROIE dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--split',
        type=str,
        choices=['train', 'test'],
        default='train',
        help='Dataset split to evaluate (default: train)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of samples to evaluate (default: all)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file path (default: no file output)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed metrics'
    )
    
    parser.add_argument(
        '--show-calibration',
        action='store_true',
        help='Show confidence calibration analysis'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable OCR result caching'
    )
    
    args = parser.parse_args()
    
    # Print configuration
    print_section_header("EVALUATION CONFIGURATION")
    print(f"Dataset Split:     {args.split}")
    print(f"Sample Limit:      {args.limit if args.limit else 'All'}")
    print(f"OCR Cache:         {'Disabled' if args.no_cache else 'Enabled'}")
    print(f"Verbose Output:    {args.verbose}")
    print(f"Show Calibration:  {args.show_calibration}")
    print()
    
    # Ensure directories exist
    Config.ensure_directories()
    
    # Initialize processor
    logger.info("Initializing document processor...")
    processor = DocumentProcessor(use_cache=not args.no_cache)
    
    # Initialize evaluator
    logger.info("Initializing evaluator...")
    evaluator = DocumentEvaluator(processor)
    
    # Run evaluation
    print_section_header("RUNNING EVALUATION")
    print("This may take several minutes...")
    print()
    
    try:
        results = evaluator.evaluate_dataset(
            split=args.split,
            limit=args.limit
        )
        
        # Print results
        print_overall_metrics(results)
        print_field_metrics(results, verbose=args.verbose)
        
        if args.show_calibration:
            print_confidence_calibration(results, show_buckets=True)
            print_calibration_interpretation(results)
        
        # Save results if requested
        if args.output:
            save_results(results, args.output)
        
        print_section_header("EVALUATION COMPLETE")
        print("✓ Evaluation finished successfully")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n✗ Evaluation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        print(f"\n✗ Evaluation failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())


# Made with Bob