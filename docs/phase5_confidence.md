# Phase 5: Confidence Scoring - Documentation

## Overview

The confidence scoring system provides meaningful, calibrated confidence scores for extracted fields by combining multiple quality factors. This enables the system to not only extract information but also assess the reliability of each extraction.

**Key Features:**
- Multi-factor confidence scoring
- Calibration framework for accuracy alignment
- Explainable confidence breakdowns
- Robust handling of edge cases
- Integration with extraction pipeline

## Why Confidence Scoring Matters

### The Problem

Raw extraction confidence scores (from heuristic matching) have several limitations:

1. **Not Calibrated**: A score of 0.8 doesn't necessarily mean 80% accuracy
2. **Single-Factor**: Only considers extraction heuristics, ignoring other quality signals
3. **No OCR Quality**: Doesn't account for OCR confidence or text quality
4. **No Validation**: Doesn't check if extracted values are reasonable

### The Solution

Our multi-factor confidence scorer combines:
- **Extraction confidence** (40%): From heuristic matching
- **OCR quality** (30%): Text clarity and OCR engine confidence
- **Value validity** (20%): Format and range checks
- **Pattern strength** (10%): How well values match expected patterns

This produces more meaningful scores that better correlate with actual accuracy.

## Architecture

### Component Hierarchy

```
ConfidenceManager
├── MultiFactorConfidenceScorer
│   ├── OCR Quality Calculator
│   ├── Validity Checker
│   └── Pattern Matcher
└── ConfidenceCalibrator
    └── Calibration Bins
```

### Class Diagram

```
┌─────────────────────┐
│  ConfidenceScorer   │ (Abstract)
│  ─────────────────  │
│  + calculate_conf() │
└──────────┬──────────┘
           │
           │ implements
           ▼
┌──────────────────────────────┐
│ MultiFactorConfidenceScorer  │
│ ──────────────────────────── │
│ - weights: Dict              │
│ + calculate_confidence()     │
│ + _calculate_ocr_quality()   │
│ + _calculate_validity()      │
│ + _calculate_pattern()       │
└──────────────────────────────┘

┌──────────────────────────────┐
│   ConfidenceCalibrator       │
│ ──────────────────────────── │
│ - calibration_bins: Dict     │
│ + fit()                      │
│ + calibrate()                │
└──────────────────────────────┘

┌──────────────────────────────┐
│    ConfidenceManager         │
│ ──────────────────────────── │
│ - scorer: Scorer             │
│ - calibrator: Calibrator     │
│ + score_extraction()         │
└──────────────────────────────┘
```

## Multi-Factor Approach

### Factor 1: Extraction Confidence (40%)

**Source**: Heuristic matching from field extractor

**What it measures**:
- Keyword proximity to extracted value
- Position on document
- Format matching

**Example**:
```python
# High extraction confidence
"Total: $4.95" → 0.95 (keyword "Total" nearby, clear format)

# Low extraction confidence  
"4.95" → 0.60 (no context, ambiguous)
```

### Factor 2: OCR Quality (30%)

**Source**: OCR engine metadata

**What it measures**:
- OCR engine confidence scores
- Text length (longer text = more reliable OCR)
- Character density

**Calculation**:
```python
def calculate_ocr_quality(ocr_result):
    base_confidence = ocr_result.get('confidence', 0.5)
    text_length = len(ocr_result.get('text', ''))
    length_factor = min(1.0, text_length / 500)
    
    quality = base_confidence * 0.7 + length_factor * 0.3
    return quality
```

**Why it matters**: Poor OCR quality affects all extractions, regardless of heuristic matching.

### Factor 3: Value Validity (20%)

**Source**: Domain knowledge and validation rules

**What it measures**:
- Format correctness
- Range reasonableness
- Logical consistency

**Validation Rules**:

#### Date Validation
```python
def validate_date(date_str):
    # Parse date
    date_obj = datetime.fromisoformat(date_str)
    
    # Check year range (1900-2100)
    if not (1900 <= date_obj.year <= 2100):
        return 0.3  # Invalid year
    
    # Check not too far in future (allow 1 year)
    max_future = datetime.now() + timedelta(days=365)
    if date_obj <= max_future:
        return 1.0  # Valid
    
    return 0.7  # Future date but valid format
```

#### Total Validation
```python
def validate_total(amount):
    if amount <= 0:
        return 0.0  # Invalid
    
    if 0.01 <= amount <= 100000:
        # Penalize suspiciously round numbers
        if amount == round(amount) and amount >= 100:
            return 0.8  # Might be subtotal
        return 1.0  # Valid
    
    if amount > 100000:
        return 0.5  # Unusually high
    
    return 0.3  # Too small
```

#### Invoice Number Validation
```python
def validate_invoice_number(invoice_num):
    # Check length (3-30 chars)
    if not (3 <= len(invoice_num) <= 30):
        return 0.3
    
    # Must contain alphanumeric
    if not re.search(r'[a-zA-Z0-9]', invoice_num):
        return 0.0
    
    # Check alphanumeric ratio
    alnum_ratio = sum(c.isalnum() for c in invoice_num) / len(invoice_num)
    if alnum_ratio >= 0.5:
        return 1.0
    elif alnum_ratio >= 0.3:
        return 0.7
    else:
        return 0.4
```

### Factor 4: Pattern Strength (10%)

**Source**: Pattern matching against expected formats

**What it measures**:
- How well the value matches standard patterns
- Format consistency

**Pattern Scoring**:

#### Date Patterns
```python
patterns = [
    (r'\d{2}/\d{2}/\d{4}', 1.0),      # DD/MM/YYYY (most common)
    (r'\d{4}-\d{2}-\d{2}', 0.95),     # YYYY-MM-DD (ISO)
    (r'\d{2}-\d{2}-\d{4}', 0.9),      # DD-MM-YYYY
    (r'\d{1,2}/\d{1,2}/\d{4}', 0.85), # D/M/YYYY
]
```

#### Total Patterns
```python
patterns = [
    (r'\$\s*\d+\.\d{2}', 1.0),        # $XX.XX (best)
    (r'\d+\.\d{2}', 0.9),             # XX.XX
    (r'\$\s*\d+,\d{3}\.\d{2}', 0.95), # $X,XXX.XX
]
```

#### Invoice Patterns
```python
patterns = [
    (r'INV[-\s]?\d+', 1.0),           # INV-XXX (standard)
    (r'#\d+', 0.95),                  # #XXX
    (r'[A-Z]{2,4}[-\s]?\d+', 0.9),    # ABC-XXX
]
```

## Factor Weights

### Why These Weights?

```python
weights = {
    'extraction': 0.4,    # 40% - Primary signal
    'ocr_quality': 0.3,   # 30% - Foundation quality
    'validity': 0.2,      # 20% - Sanity check
    'pattern': 0.1        # 10% - Format bonus
}
```

**Rationale**:

1. **Extraction (40%)**: Highest weight because it directly measures how well we found the field
2. **OCR Quality (30%)**: Second highest because poor OCR affects everything
3. **Validity (20%)**: Important sanity check but shouldn't override strong extraction
4. **Pattern (10%)**: Nice-to-have bonus for standard formats

### Sensitivity Analysis

Impact of changing weights:

| Scenario | Extraction | OCR | Validity | Pattern | Result |
|----------|-----------|-----|----------|---------|--------|
| Strong extraction, poor OCR | 0.9 | 0.4 | 0.8 | 0.7 | 0.70 |
| Weak extraction, good OCR | 0.5 | 0.9 | 0.9 | 0.8 | 0.68 |
| Good all around | 0.8 | 0.8 | 0.9 | 0.9 | 0.83 |
| Poor all around | 0.4 | 0.4 | 0.5 | 0.4 | 0.43 |

## Calibration Strategy

### Why Calibration?

Raw confidence scores don't directly correspond to accuracy:

```
Raw Score 0.8 → Actual Accuracy 65%  ❌ Overconfident
Raw Score 0.9 → Actual Accuracy 85%  ✓ Better aligned
```

Calibration maps raw scores to actual accuracy using validation data.

### Calibration Method: Binning

We use simple binning (isotonic regression alternative):

```python
# Example calibration bins for date field
DATE_BINS = [
    (0.0, 0.0),   # Raw 0.0-0.3 → Calibrated 0%
    (0.3, 0.4),   # Raw 0.3-0.5 → Calibrated 40%
    (0.5, 0.6),   # Raw 0.5-0.7 → Calibrated 60%
    (0.7, 0.75),  # Raw 0.7-0.8 → Calibrated 75%
    (0.8, 0.85),  # Raw 0.8-0.9 → Calibrated 85%
    (0.9, 0.92),  # Raw 0.9-1.0 → Calibrated 92%
]
```

### Calibration Process

1. **Collect Data**: Run extraction on validation set
2. **Bin Scores**: Group predictions by confidence ranges
3. **Calculate Accuracy**: Measure actual accuracy per bin
4. **Create Mapping**: Map raw scores to calibrated scores
5. **Apply**: Use mapping for future predictions

### Expected Calibration Error (ECE)

Measures calibration quality:

```python
def calculate_ece(bins):
    """Lower is better (0 = perfect calibration)"""
    total_samples = sum(b['count'] for b in bins)
    ece = 0.0
    
    for bin_data in bins:
        weight = bin_data['count'] / total_samples
        error = abs(bin_data['avg_confidence'] - bin_data['accuracy'])
        ece += weight * error
    
    return ece
```

**Target ECE**: < 0.10 (10% average error)

## Validation Methodology

### Metrics

1. **Accuracy**: % of correct extractions
2. **Calibration Error**: Difference between confidence and accuracy
3. **Confidence Distribution**: Spread of confidence scores
4. **Factor Correlation**: How each factor correlates with accuracy

### Validation Process

```bash
# Analyze confidence on validation set
python scripts/analyze_confidence.py --samples 100

# Generate calibration data
python scripts/analyze_confidence.py --calibrate --output calibration.json

# Compare calibrated vs uncalibrated
python scripts/analyze_confidence.py --compare
```

### Expected Results

Based on Phase 4 extraction accuracy:

| Field | Extraction Accuracy | Expected Confidence Range | Calibrated Confidence |
|-------|-------------------|--------------------------|---------------------|
| Date | 85-90% | 0.75-0.95 | 0.80-0.92 |
| Total | 80-85% | 0.70-0.90 | 0.75-0.88 |
| Invoice | 75-80% | 0.65-0.85 | 0.70-0.85 |

## Interpretation Guide

### What Confidence Scores Mean

| Confidence Range | Interpretation | Action |
|-----------------|----------------|--------|
| 0.90 - 1.00 | Very High | Trust extraction, use directly |
| 0.75 - 0.90 | High | Likely correct, minimal review |
| 0.60 - 0.75 | Medium | Review recommended |
| 0.40 - 0.60 | Low | Manual verification required |
| 0.00 - 0.40 | Very Low | Likely incorrect, re-extract |

### Confidence Factor Analysis

When debugging low confidence:

```python
{
    'confidence': 0.65,
    'confidence_factors': {
        'extraction': 0.85,  # ✓ Good extraction
        'ocr_quality': 0.45, # ❌ Poor OCR (root cause)
        'validity': 0.90,    # ✓ Valid value
        'pattern': 0.80      # ✓ Good pattern
    }
}
```

**Diagnosis**: Low confidence due to poor OCR quality. Consider:
- Image preprocessing
- Different OCR engine
- Manual review

## Usage Examples

### Basic Usage

```python
from pipeline.extractor import ExtractionManager
from pipeline.confidence import ConfidenceManager
from pipeline.ocr import OCRManager

# Initialize components
ocr_engine = OCRManager()
extractor = ExtractionManager()
confidence_mgr = ConfidenceManager(use_calibration=False)

# Process document
ocr_result = ocr_engine.extract_text('receipt.jpg')
extraction_results = extractor.extract_fields(ocr_result)

# Score confidence
scored_results = confidence_mgr.score_extraction(
    extraction_results,
    ocr_result
)

# Access results
print(f"Date: {scored_results['date']['value']}")
print(f"Confidence: {scored_results['date']['confidence']:.2%}")
print(f"Factors: {scored_results['date']['confidence_factors']}")
```

### With Calibration

```python
from pipeline.confidence import ConfidenceManager, ConfidenceCalibrator

# Train calibrator
calibrator = ConfidenceCalibrator()
calibrator.fit(predictions, ground_truth)

# Use calibrated confidence
confidence_mgr = ConfidenceManager(
    use_calibration=True,
    calibrator=calibrator
)

scored_results = confidence_mgr.score_extraction(
    extraction_results,
    ocr_result
)

# Calibrated confidence is more accurate
print(f"Raw: {scored_results['date']['raw_confidence']:.3f}")
print(f"Calibrated: {scored_results['date']['confidence']:.3f}")
```

### Batch Processing

```python
from pathlib import Path

def process_batch(image_paths, confidence_threshold=0.75):
    """Process batch with confidence filtering."""
    results = []
    
    for image_path in image_paths:
        # Extract and score
        ocr_result = ocr_engine.extract_text(image_path)
        extraction = extractor.extract_fields(ocr_result)
        scored = confidence_mgr.score_extraction(extraction, ocr_result)
        
        # Filter by confidence
        high_conf_fields = {
            field: data
            for field, data in scored.items()
            if field != 'metadata' and data['confidence'] >= confidence_threshold
        }
        
        results.append({
            'image': image_path,
            'fields': high_conf_fields,
            'needs_review': len(high_conf_fields) < 3
        })
    
    return results
```

### Custom Confidence Scorer

```python
from pipeline.confidence import ConfidenceScorer

class CustomScorer(ConfidenceScorer):
    """Custom scorer with different weights."""
    
    def __init__(self):
        self.weights = {
            'extraction': 0.5,  # Higher weight on extraction
            'ocr_quality': 0.2,
            'validity': 0.2,
            'pattern': 0.1
        }
    
    def calculate_confidence(self, extraction_result, ocr_result, field_name):
        # Custom logic here
        pass

# Use custom scorer
from pipeline.confidence import ConfidenceManager
confidence_mgr = ConfidenceManager()
confidence_mgr.scorer = CustomScorer()
```

## Known Limitations

### 1. Calibration Data Requirements

**Issue**: Calibration requires sufficient validation data (50+ samples per field)

**Impact**: With limited data, calibration may not improve accuracy

**Mitigation**: Use default bins or disable calibration for small datasets

### 2. Domain Specificity

**Issue**: Validation rules are tuned for receipts/invoices

**Impact**: May not work well for other document types

**Mitigation**: Adjust validation rules and patterns for your domain

### 3. OCR Quality Dependency

**Issue**: Confidence heavily depends on OCR quality

**Impact**: Poor OCR can mask good extraction

**Mitigation**: 
- Use high-quality OCR engines
- Apply image preprocessing
- Consider OCR confidence thresholds

### 4. Pattern Matching Limitations

**Issue**: Pattern matching is regex-based and may miss variations

**Impact**: Lower pattern scores for non-standard formats

**Mitigation**: Add more patterns or reduce pattern weight

### 5. Overconfidence in Edge Cases

**Issue**: System may be overconfident on ambiguous cases

**Impact**: False sense of accuracy

**Mitigation**:
- Use calibration
- Set conservative confidence thresholds
- Always validate high-stakes extractions

### 6. Computational Overhead

**Issue**: Multi-factor scoring adds processing time

**Impact**: ~2-5ms per document

**Mitigation**: Acceptable for most use cases; optimize if needed

## Performance Characteristics

### Timing

Typical processing times per document:

| Component | Time | % of Total |
|-----------|------|-----------|
| OCR | 500-1000ms | 95% |
| Extraction | 10-20ms | 2% |
| Confidence Scoring | 2-5ms | <1% |
| **Total** | **512-1025ms** | **100%** |

Confidence scoring adds minimal overhead (<1% of total time).

### Memory

Memory usage per document:

- Confidence scorer: ~1KB
- Calibrator: ~10KB (with bins)
- Results: ~2KB per document

Total: ~13KB per document (negligible)

### Scalability

The system scales linearly:

- 1,000 documents: ~10 minutes
- 10,000 documents: ~100 minutes
- 100,000 documents: ~1,000 minutes (~17 hours)

Bottleneck is OCR, not confidence scoring.

## Best Practices

### 1. Always Use Calibration in Production

```python
# ✓ Good: Use calibration
confidence_mgr = ConfidenceManager(use_calibration=True, calibrator=calibrator)

# ❌ Bad: Skip calibration
confidence_mgr = ConfidenceManager(use_calibration=False)
```

### 2. Set Appropriate Thresholds

```python
# Different thresholds for different use cases
THRESHOLDS = {
    'auto_process': 0.90,  # Very high confidence
    'light_review': 0.75,  # High confidence
    'full_review': 0.60,   # Medium confidence
    'reject': 0.40         # Low confidence
}
```

### 3. Monitor Confidence Distribution

```python
# Track confidence over time
def monitor_confidence(scored_results):
    confidences = [
        data['confidence']
        for field, data in scored_results.items()
        if field != 'metadata'
    ]
    
    avg_conf = sum(confidences) / len(confidences)
    
    # Alert if confidence drops
    if avg_conf < 0.70:
        logger.warning(f"Low average confidence: {avg_conf:.2%}")
```

### 4. Analyze Factor Breakdowns

```python
# Identify systematic issues
def analyze_factors(batch_results):
    factor_avgs = {
        'extraction': [],
        'ocr_quality': [],
        'validity': [],
        'pattern': []
    }
    
    for result in batch_results:
        for field, data in result.items():
            if field != 'metadata':
                for factor, value in data['confidence_factors'].items():
                    factor_avgs[factor].append(value)
    
    # Find weak factors
    for factor, values in factor_avgs.items():
        avg = sum(values) / len(values)
        if avg < 0.70:
            logger.warning(f"Low {factor}: {avg:.2%}")
```

### 5. Recalibrate Periodically

```python
# Recalibrate every N documents or M days
def should_recalibrate(last_calibration_date, documents_processed):
    days_since = (datetime.now() - last_calibration_date).days
    return days_since > 30 or documents_processed > 1000
```

## Future Enhancements

### Potential Improvements

1. **Machine Learning Calibration**: Use isotonic regression or Platt scaling
2. **Field-Specific Weights**: Different weights per field type
3. **Context-Aware Scoring**: Consider document-level context
4. **Ensemble Scoring**: Combine multiple scoring methods
5. **Active Learning**: Use confidence to select samples for labeling
6. **Uncertainty Quantification**: Provide confidence intervals

### Research Directions

1. **Confidence Explanation**: Generate natural language explanations
2. **Adversarial Testing**: Test robustness to edge cases
3. **Cross-Domain Transfer**: Adapt to new document types
4. **Real-Time Calibration**: Update calibration online

## Conclusion

The confidence scoring system provides:

✓ **Meaningful scores** that correlate with accuracy  
✓ **Explainable breakdowns** for debugging  
✓ **Calibration framework** for accuracy alignment  
✓ **Robust handling** of edge cases  
✓ **Easy integration** with extraction pipeline  

This enables confident automation with appropriate human oversight.

---

**Phase 5 Complete** ✓

Next: Phase 6 - Pipeline Integration