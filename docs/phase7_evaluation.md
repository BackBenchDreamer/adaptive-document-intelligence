# Phase 7: Evaluation System

## Overview

The evaluation system provides comprehensive metrics for measuring the Adaptive Document Intelligence System's performance on the SROIE dataset. It includes accuracy metrics, confidence calibration analysis, and detailed per-field performance tracking.

## Architecture

```
tests/metrics/
├── __init__.py
├── evaluation.py          # Main evaluation module
    ├── MetricsCalculator           # Compute accuracy metrics
    ├── ConfidenceCalibrationAnalyzer  # Analyze confidence quality
    └── DocumentEvaluator           # End-to-end evaluation

scripts/
└── run_evaluation.py      # CLI for running evaluations

tests/unit/
└── test_evaluation.py     # Unit tests
```

## Components

### 1. MetricsCalculator

Computes various evaluation metrics:

**Basic Metrics:**
- **Accuracy**: Exact match rate
- **Precision**: Correct extractions / Total extractions
- **Recall**: Correct extractions / Total ground truth
- **F1 Score**: Harmonic mean of precision and recall

**Specialized Metrics:**
- **Fuzzy Match**: String similarity using Levenshtein distance
- **Date Accuracy**: Date matching with optional tolerance
- **Amount Accuracy**: Numeric matching with percentage tolerance

**Example:**
```python
from tests.metrics.evaluation import MetricsCalculator

calculator = MetricsCalculator()

# Calculate accuracy
predictions = ['2018-03-30', '2018-04-15', '2018-05-20']
ground_truth = ['2018-03-30', '2018-04-15', '2018-05-21']
accuracy = calculator.calculate_accuracy(predictions, ground_truth)
# accuracy = 0.667 (2 out of 3 correct)

# Calculate precision, recall, F1
precision, recall, f1 = calculator.calculate_precision_recall_f1(
    predictions, ground_truth
)

# Fuzzy string matching
fuzzy_accuracy = calculator.calculate_fuzzy_match(
    predictions, ground_truth, threshold=0.8
)
```

### 2. ConfidenceCalibrationAnalyzer

Analyzes whether confidence scores correlate with actual accuracy.

**Confidence Buckets:**
- **Very Low**: 0.0 - 0.3
- **Low**: 0.3 - 0.6
- **Medium**: 0.6 - 0.8
- **High**: 0.8 - 0.9
- **Very High**: 0.9 - 1.0

**Expected Calibration Error (ECE):**
Measures the difference between confidence and accuracy across buckets.
- ECE < 0.1: Well calibrated
- ECE 0.1-0.2: Moderately calibrated
- ECE > 0.2: Poorly calibrated

**Example:**
```python
from tests.metrics.evaluation import ConfidenceCalibrationAnalyzer

analyzer = ConfidenceCalibrationAnalyzer()

predictions = ['a', 'b', 'c', 'd', 'e']
ground_truth = ['a', 'b', 'x', 'd', 'e']
confidences = [0.95, 0.90, 0.85, 0.75, 0.70]

result = analyzer.analyze_calibration(
    predictions, ground_truth, confidences, 'date'
)

print(f"ECE: {result['expected_calibration_error']:.4f}")
print(f"Well calibrated: {result['is_well_calibrated']}")

# Analyze by bucket
for bucket_name, data in result['by_bucket'].items():
    print(f"{bucket_name}: {data['count']} samples, "
          f"{data['accuracy']:.2%} accuracy")
```

### 3. DocumentEvaluator

End-to-end evaluation on SROIE dataset.

**Features:**
- Processes entire dataset
- Computes per-field metrics
- Analyzes confidence calibration
- Tracks processing time
- Handles errors gracefully

**Example:**
```python
from pipeline.pipeline import DocumentProcessor
from tests.metrics.evaluation import DocumentEvaluator

# Initialize processor and evaluator
processor = DocumentProcessor(ocr_engine='tesseract')
evaluator = DocumentEvaluator(processor)

# Evaluate on training set
results = evaluator.evaluate_dataset(split='train', limit=100)

# Access results
print(f"Overall accuracy: {results['overall']['accuracy']:.2%}")
print(f"Date accuracy: {results['per_field']['date']['accuracy']:.2%}")
print(f"Total accuracy: {results['per_field']['total']['accuracy']:.2%}")
```

## Metrics Definitions

### Accuracy
Percentage of exact matches between predictions and ground truth.

```
Accuracy = Correct Predictions / Total Predictions
```

### Precision
Of all extractions made, how many were correct?

```
Precision = True Positives / (True Positives + False Positives)
```

### Recall
Of all ground truth values, how many were extracted correctly?

```
Recall = True Positives / (True Positives + False Negatives)
```

### F1 Score
Harmonic mean of precision and recall.

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

### Expected Calibration Error (ECE)
Average difference between confidence and accuracy across buckets.

```
ECE = Σ (|confidence_bucket - accuracy_bucket| × bucket_weight)
```

## Usage Examples

### Basic Evaluation

```bash
# Evaluate on full training set
python scripts/run_evaluation.py --split train

# Evaluate on subset (faster)
python scripts/run_evaluation.py --split train --limit 100

# Evaluate on test set
python scripts/run_evaluation.py --split test
```

### With Options

```bash
# Show detailed metrics
python scripts/run_evaluation.py --split train --verbose

# Show confidence calibration analysis
python scripts/run_evaluation.py --split train --show-calibration

# Save results to JSON
python scripts/run_evaluation.py --split train --output results.json

# Disable caching (slower but fresh results)
python scripts/run_evaluation.py --split train --no-cache
```

### Programmatic Usage

```python
from pipeline.pipeline import DocumentProcessor
from tests.metrics.evaluation import DocumentEvaluator

# Initialize
processor = DocumentProcessor(ocr_engine='tesseract', use_cache=True)
evaluator = DocumentEvaluator(processor)

# Run evaluation
results = evaluator.evaluate_dataset(split='train', limit=50)

# Print summary
print(f"Samples: {results['samples_evaluated']}")
print(f"Time: {results['processing_time']:.2f}s")
print(f"Overall: {results['overall']['accuracy']:.2%}")

# Per-field results
for field, metrics in results['per_field'].items():
    print(f"\n{field.upper()}:")
    print(f"  Accuracy:  {metrics['accuracy']:.2%}")
    print(f"  Precision: {metrics['precision']:.2%}")
    print(f"  Recall:    {metrics['recall']:.2%}")
    print(f"  F1:        {metrics['f1']:.2%}")

# Confidence calibration
for field, analysis in results['confidence_analysis'].items():
    print(f"\n{field.upper()} Calibration:")
    print(f"  ECE: {analysis['expected_calibration_error']:.4f}")
    print(f"  Well calibrated: {analysis['is_well_calibrated']}")
```

## Interpreting Results

### Good Results

**Accuracy Metrics:**
- Date accuracy > 85%
- Total accuracy > 80%
- F1 score > 0.85

**Confidence Calibration:**
- ECE < 0.1
- High confidence predictions (0.9-1.0) have >90% accuracy
- Confidence increases with accuracy across buckets

**Example Output:**
```
DATE:
  Accuracy:  89.2%
  Precision: 90.5%
  Recall:    98.5%
  F1:        94.3%
  
DATE Calibration:
  ECE: 0.042
  Well calibrated: ✓ Yes
  
  Confidence Buckets:
  very_high (0.9-1.0): 135 samples, 95% accuracy
  high (0.8-0.9):      256 samples, 88% accuracy
  medium (0.6-0.8):    178 samples, 74% accuracy
```

### Warning Signs

**Poor Accuracy:**
- Date accuracy < 70%
- Total accuracy < 65%
- Large gap between precision and recall

**Poor Calibration:**
- ECE > 0.2
- High confidence predictions have low accuracy (overconfident)
- Confidence doesn't correlate with accuracy

**Example Output:**
```
TOTAL:
  Accuracy:  62.4%
  Precision: 65.2%
  Recall:    95.8%
  F1:        77.5%
  
TOTAL Calibration:
  ECE: 0.287
  Well calibrated: ✗ No
  WARNING: Large calibration error detected!
  
  Confidence Buckets:
  very_high (0.9-1.0): 89 samples, 68% accuracy  ⚠ Overconfident!
  high (0.8-0.9):      145 samples, 71% accuracy
```

## Confidence Calibration

### What is Calibration?

A well-calibrated system has confidence scores that match actual accuracy:
- 90% confidence → 90% accuracy
- 70% confidence → 70% accuracy
- 50% confidence → 50% accuracy

### Why It Matters

**Well-calibrated confidence enables:**
1. **Reliable filtering**: Reject low-confidence predictions
2. **Human review**: Prioritize uncertain cases
3. **Downstream decisions**: Trust high-confidence outputs
4. **System monitoring**: Detect performance degradation

### Calibration Analysis

The system analyzes calibration by:

1. **Grouping predictions by confidence bucket**
2. **Computing accuracy for each bucket**
3. **Comparing confidence vs. accuracy**
4. **Calculating Expected Calibration Error (ECE)**

### Interpreting ECE

| ECE Range | Interpretation | Action |
|-----------|----------------|--------|
| < 0.05 | Excellent calibration | No action needed |
| 0.05-0.10 | Good calibration | Monitor |
| 0.10-0.20 | Moderate calibration | Consider recalibration |
| > 0.20 | Poor calibration | Recalibration needed |

### Common Calibration Issues

**Overconfidence:**
- High confidence but low accuracy
- System is too optimistic
- Solution: Apply temperature scaling or Platt scaling

**Underconfidence:**
- Low confidence but high accuracy
- System is too pessimistic
- Solution: Boost confidence scores

**Inconsistent:**
- No correlation between confidence and accuracy
- Solution: Redesign confidence scoring

## Known Limitations

### Evaluation Limitations

1. **Ground Truth Quality**: Assumes SROIE annotations are perfect
2. **Exact Match**: May be too strict for some fields
3. **Limited Fields**: Only evaluates date and total
4. **No Error Analysis**: Doesn't categorize error types (Phase 8)

### Metric Limitations

1. **Accuracy**: Doesn't distinguish error types
2. **Precision/Recall**: Treats all errors equally
3. **Fuzzy Match**: Threshold is arbitrary
4. **Date Tolerance**: May hide systematic errors

### Calibration Limitations

1. **Bucket Size**: Small buckets have high variance
2. **ECE**: Sensitive to bucket boundaries
3. **Binary**: Doesn't capture confidence distribution
4. **Dataset-Specific**: May not generalize

## Troubleshooting

### Low Accuracy

**Problem**: Overall accuracy < 70%

**Possible Causes:**
1. OCR quality issues
2. Extraction heuristics too strict
3. Ground truth format mismatch
4. Preprocessing problems

**Solutions:**
1. Check OCR confidence scores
2. Review extraction patterns
3. Verify date/amount normalization
4. Try different OCR engine

### Poor Calibration

**Problem**: ECE > 0.2

**Possible Causes:**
1. Confidence scoring too simplistic
2. OCR confidence unreliable
3. Extraction confidence not informative
4. Imbalanced confidence distribution

**Solutions:**
1. Implement confidence calibration
2. Use multiple confidence factors
3. Apply temperature scaling
4. Collect more diverse data

### Slow Evaluation

**Problem**: Evaluation takes too long

**Solutions:**
1. Enable caching: `--no-cache` flag off
2. Use smaller subset: `--limit 100`
3. Use faster OCR engine: Tesseract instead of PaddleOCR
4. Disable preprocessing
5. Use parallel processing (future enhancement)

### Memory Issues

**Problem**: Out of memory during evaluation

**Solutions:**
1. Evaluate in smaller batches
2. Clear cache between runs
3. Use `--limit` to reduce dataset size
4. Close other applications

## Performance Benchmarks

### Expected Performance (Tesseract)

**Accuracy:**
- Date: 85-90%
- Total: 80-85%
- Overall: 82-87%

**Calibration:**
- ECE: 0.05-0.10
- Well calibrated: Yes

**Speed:**
- Processing: 0.8s per image
- Full dataset (626 images): ~8-10 minutes

### Expected Performance (PaddleOCR)

**Accuracy:**
- Date: 90-95%
- Total: 85-90%
- Overall: 87-92%

**Calibration:**
- ECE: 0.04-0.08
- Well calibrated: Yes

**Speed:**
- Processing: 1.5s per image (CPU)
- Full dataset: ~15-20 minutes

## Future Enhancements

### Phase 8: Error Analysis
- Categorize error types
- Identify systematic failures
- Generate error reports

### Phase 9: Testing Framework
- Automated regression testing
- Performance benchmarking
- Continuous evaluation

### Advanced Features
- Cross-validation
- Statistical significance testing
- Confidence calibration methods
- Multi-dataset evaluation
- Visualization tools

## References

### Calibration
- Guo et al. (2017): "On Calibration of Modern Neural Networks"
- Platt (1999): "Probabilistic Outputs for Support Vector Machines"

### Metrics
- Manning & Schütze (1999): "Foundations of Statistical NLP"
- Sokolova & Lapalme (2009): "A systematic analysis of performance measures"

### SROIE Dataset
- Huang et al. (2019): "ICDAR2019 Competition on Scanned Receipt OCR and Information Extraction"

## Made with Bob