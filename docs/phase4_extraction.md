# Phase 4: Field Extraction Engine

**Status:** ✅ Complete  
**Date:** 2026-04-27  
**Module:** `pipeline/extractor.py`

## Overview

The Field Extraction Engine extracts structured fields (date, total, invoice_number) from noisy OCR text using heuristic-based scoring methods. This is a critical component that transforms raw OCR text into structured, actionable data.

### Key Features

- **Heuristic-Based Extraction**: Uses pattern matching and scoring (no ML models)
- **Multi-Field Support**: Extracts date, total amount, and invoice number
- **Robust Scoring**: Combines multiple signals (keywords, position, format)
- **Explainable Results**: Every extraction decision is traceable
- **Confidence Scores**: Returns confidence for each extracted field
- **Edge Case Handling**: Handles multiple candidates, ambiguous text, and noise

## Architecture

### Component Hierarchy

```
ExtractionManager
├── DateExtractor
├── TotalExtractor
└── InvoiceNumberExtractor
```

Each extractor inherits from the abstract `FieldExtractor` base class and implements field-specific logic.

## Extraction Pipeline

### High-Level Flow

```
OCR Text → Field Extractors → Scored Candidates → Best Selection → Structured Output
```

### Detailed Process

1. **Candidate Discovery**: Find all potential matches using regex patterns
2. **Scoring**: Score each candidate based on multiple factors
3. **Selection**: Choose highest-scoring candidate
4. **Normalization**: Convert to standard format (ISO date, float amount, etc.)
5. **Result Packaging**: Return value with confidence and metadata

## Field-Specific Strategies

### 1. Date Extraction

**Objective**: Extract invoice/receipt date from text

**Supported Formats**:
- `DD/MM/YYYY`, `MM/DD/YYYY` (e.g., 30/03/2018)
- `DD-MM-YYYY`, `MM-DD-YYYY` (e.g., 30-03-2018)
- `YYYY-MM-DD` (e.g., 2018-03-30)
- `DD Mon YYYY` (e.g., 30 March 2018)
- `Mon DD YYYY` (e.g., March 30, 2018)
- Compact: `DDMMYYYY`, `YYYYMMDD` (e.g., 30032018)

**Scoring Factors**:

| Factor | Weight | Description |
|--------|--------|-------------|
| Keyword Proximity | 40% | Distance to keywords like "date", "invoice date" |
| Position Bias | 30% | Preference for top 30% of document |
| Format Validity | 20% | Pattern match strength and format reliability |
| Context | 10% | Presence of colons, labels, or date-related text |

**Keyword List**:
- Positive: `date`, `invoice date`, `receipt date`, `issued`, `dated`, `on`, `as of`, `bill date`, `transaction date`

**Example**:
```python
text = "Invoice Date: 30/03/2018\nTotal: $10.50"

# Candidates found:
# - "30/03/2018" at position 15

# Scoring:
# - Keyword proximity: 1.0 (near "Invoice Date")
# - Position: 1.0 (in top 30%)
# - Format: 1.0 (standard DD/MM/YYYY)
# - Context: 1.0 (after colon)
# Final score: 0.4 + 0.3 + 0.2 + 0.1 = 1.0

# Result: 2018-03-30 (confidence: 1.0)
```

### 2. Total Amount Extraction

**Objective**: Extract total amount from receipt (most critical field)

**Challenges**:
- Multiple amounts on receipt (items, subtotal, tax, total)
- Distinguishing total from subtotal
- Handling currency symbols and separators
- Avoiding "change" or "tendered" amounts

**Patterns Detected**:
- With currency: `$10.50`, `€10.50`, `£10.50`
- Without currency: `10.50`, `1,234.56`
- Various formats: `10.5`, `10.50`, `1,234.56`

**Scoring Factors**:

| Factor | Weight | Description |
|--------|--------|-------------|
| Keyword Proximity | 40% | Distance to "total", "amount due", "balance" |
| Position Bias | 30% | Preference for bottom 40% of document |
| Format Validity | 20% | Currency symbol presence, decimal format |
| Magnitude Bonus | 10% | Bonus if largest amount (likely total) |
| Penalties | -50% | Near "subtotal", "tax", "discount", "change" |

**Keyword Lists**:
- Positive: `total`, `amount due`, `balance`, `grand total`, `net total`, `amount`, `pay`, `payment`, `due`, `payable`
- Negative: `subtotal`, `sub total`, `sub-total`, `tax`, `gst`, `vat`, `discount`, `change`, `tendered`, `cash`, `card`, `paid`

**Example**:
```python
text = """
Item 1: $5.00
Item 2: $3.50
Subtotal: $8.50
Tax: $1.50
Total: $10.00
"""

# Candidates found:
# - $5.00 (score: 0.3)
# - $3.50 (score: 0.3)
# - $8.50 (score: 0.2, penalty for "subtotal")
# - $1.50 (score: 0.2, penalty for "tax")
# - $10.00 (score: 0.9, near "Total", bottom position)

# Result: 10.00 (confidence: 0.9)
```

### 3. Invoice Number Extraction

**Objective**: Extract invoice/receipt number (optional field)

**Patterns Detected**:
- With prefix: `INV-12345`, `REC-67890`
- With symbol: `#123456`
- After keyword: `Invoice Number: ABC123XYZ`
- Standalone: `ABC12345` (6-15 characters)

**Scoring Factors**:

| Factor | Weight | Description |
|--------|--------|-------------|
| Keyword Proximity | 50% | Distance to "invoice", "receipt", "no", "#" |
| Position Bias | 30% | Preference for top 30% of document |
| Format Validity | 20% | Length (6-12 chars), alphanumeric mix |

**Keyword List**:
- Positive: `invoice`, `receipt`, `no`, `number`, `#`, `ref`, `reference`, `bill`, `transaction`, `order`

**Example**:
```python
text = "Invoice No: INV-12345\nDate: 01/01/2020\nTotal: $10.00"

# Candidates found:
# - "INV-12345" at position 12

# Scoring:
# - Keyword proximity: 1.0 (near "Invoice No")
# - Position: 1.0 (in top 30%)
# - Format: 1.0 (good length, alphanumeric)
# Final score: 0.5 + 0.3 + 0.2 = 1.0

# Result: INV-12345 (confidence: 1.0)
```

## Scoring Function Design

### General Scoring Formula

```python
score = (
    keyword_match * 0.4 +
    position_score * 0.3 +
    format_score * 0.2 +
    context_score * 0.1
) - penalties
```

### Position Scoring

Position in document affects scoring based on field type:

**Date** (top-biased):
```python
relative_pos = position / text_length
score = 1.0 if relative_pos < 0.3 else 0.5
```

**Total** (bottom-biased):
```python
relative_pos = position / text_length
score = 1.0 if relative_pos > 0.6 else 0.5
```

**Invoice Number** (top-biased):
```python
relative_pos = position / text_length
score = 1.0 if relative_pos < 0.3 else 0.5
```

### Keyword Proximity

Checks for keywords within a context window (30-50 characters):

```python
context_window = 50
context_start = max(0, position - context_window)
context_end = min(text_length, position + len(candidate) + context_window)
context = text[context_start:context_end].lower()

for keyword in positive_keywords:
    if keyword in context:
        return 1.0
return 0.0
```

## Output Format

### Extraction Result Structure

```python
{
    'date': {
        'value': '2018-03-30',      # ISO format or None
        'confidence': 0.85,          # [0, 1]
        'raw_value': '30/03/2018',   # Original text
        'method': 'keyword_proximity'
    },
    'total': {
        'value': 10.00,              # Float or None
        'confidence': 0.92,
        'raw_value': '$10.00',
        'method': 'bottom_position_keyword'
    },
    'invoice_number': {
        'value': 'INV-12345',        # String or None
        'confidence': 0.75,
        'raw_value': 'INV-12345',
        'method': 'pattern_match'
    },
    'metadata': {
        'ocr_confidence': 0.88,
        'extraction_time': 0.05,
        'text_length': 450,
        'candidates_considered': {
            'date': 3,
            'total': 5,
            'invoice_number': 2
        }
    }
}
```

## Edge Cases and Handling

### 1. Multiple Date Candidates

**Scenario**: Receipt has multiple dates (issue date, due date, valid until)

**Solution**: Prefer dates near keywords like "invoice date" or "receipt date"

**Example**:
```
Receipt Date: 01/01/2020
Valid until: 31/12/2020
```
→ Extracts `01/01/2020` (higher keyword proximity score)

### 2. Subtotal vs Total Confusion

**Scenario**: Receipt has both subtotal and total

**Solution**: Apply penalty to amounts near "subtotal" keyword

**Example**:
```
Subtotal: $100.00
Tax: $10.00
Total: $110.00
```
→ Extracts `$110.00` (subtotal penalized by -0.5)

### 3. Change Amount

**Scenario**: Receipt shows change given

**Solution**: Penalize amounts near "change" or "tendered"

**Example**:
```
Total: $20.00
Cash: $50.00
Change: $30.00
```
→ Extracts `$20.00` (change penalized)

### 4. No Candidates Found

**Scenario**: No valid patterns detected

**Solution**: Return None with confidence 0.0

**Example**:
```python
{
    'value': None,
    'confidence': 0.0,
    'candidates': [],
    'method': 'no_candidates'
}
```

### 5. Invalid Date Format

**Scenario**: Date pattern found but invalid (e.g., 32/13/2020)

**Solution**: Skip invalid dates during normalization

### 6. Noisy OCR Text

**Scenario**: OCR errors create false patterns

**Solution**: Multiple scoring factors reduce impact of noise

**Example**:
```
D@te: 30/O3/2018  # 'O' instead of '0'
T0tal: $1O.OO     # '0' instead of 'O', 'O' instead of '0'
```
→ Pattern matching is flexible enough to handle some noise

## Usage Examples

### Basic Usage

```python
from pipeline.ocr import OCRManager
from pipeline.extractor import ExtractionManager

# Initialize
ocr_engine = OCRManager()
extractor = ExtractionManager()

# Process image
ocr_result = ocr_engine.extract_text('receipt.jpg')
fields = extractor.extract_fields(ocr_result)

# Access results
print(f"Date: {fields['date']['value']}")
print(f"Total: ${fields['total']['value']:.2f}")
print(f"Invoice: {fields['invoice_number']['value']}")
```

### With Confidence Thresholds

```python
# Only use high-confidence extractions
MIN_CONFIDENCE = 0.7

date = fields['date']['value'] if fields['date']['confidence'] >= MIN_CONFIDENCE else None
total = fields['total']['value'] if fields['total']['confidence'] >= MIN_CONFIDENCE else None
```

### Batch Processing

```python
from pathlib import Path

image_dir = Path('receipts/')
results = []

for image_path in image_dir.glob('*.jpg'):
    ocr_result = ocr_engine.extract_text(str(image_path))
    fields = extractor.extract_fields(ocr_result)
    results.append({
        'image': image_path.name,
        'date': fields['date']['value'],
        'total': fields['total']['value'],
        'confidence': {
            'date': fields['date']['confidence'],
            'total': fields['total']['confidence']
        }
    })
```

## Performance Expectations

### Accuracy Estimates

Based on SROIE dataset characteristics:

| Field | Expected Extraction Rate | Expected Accuracy |
|-------|-------------------------|-------------------|
| Date | 95%+ | 85-90% |
| Total | 98%+ | 80-85% |
| Invoice Number | 70-80% | 60-70% |

**Notes**:
- Date accuracy depends on format consistency
- Total accuracy affected by subtotal confusion
- Invoice number is optional and highly variable

### Processing Speed

- **Per-field extraction**: ~5-15ms
- **Full extraction (3 fields)**: ~20-50ms
- **Bottleneck**: OCR (1-3 seconds), not extraction

### Confidence Distribution

Expected confidence score distribution:

- **High confidence (>0.8)**: 60-70% of extractions
- **Medium confidence (0.5-0.8)**: 20-30% of extractions
- **Low confidence (<0.5)**: 10-20% of extractions

## Known Weaknesses

### 1. Date Format Ambiguity

**Issue**: Cannot distinguish DD/MM/YYYY from MM/DD/YYYY

**Example**: `03/04/2020` could be March 4 or April 3

**Mitigation**: Assume DD/MM/YYYY (more common in SROIE dataset)

### 2. Multiple Totals

**Issue**: Some receipts have multiple "total" labels

**Example**:
```
Total Items: 5
Total Amount: $50.00
```

**Mitigation**: Prefer amounts near "amount", "due", "balance"

### 3. Compact Date Formats

**Issue**: `DDMMYYYY` format is ambiguous

**Example**: `30032018` could be parsed incorrectly

**Mitigation**: Lower format weight (0.7 vs 1.0)

### 4. Currency Conversion

**Issue**: Does not handle currency conversion

**Example**: `€50.00` extracted as `50.00` (currency symbol lost)

**Mitigation**: Store raw_value with symbol

### 5. Handwritten Text

**Issue**: OCR struggles with handwriting, affecting extraction

**Mitigation**: Rely on OCR confidence scores

## Testing

### Unit Tests

Location: `tests/unit/test_extractor.py`

**Coverage**:
- ✅ Each extractor independently
- ✅ Multiple candidate scenarios
- ✅ Edge cases (empty text, no candidates, invalid formats)
- ✅ Real-world receipt formats
- ✅ Noisy OCR text
- ✅ Performance benchmarks

**Run tests**:
```bash
python -m pytest tests/unit/test_extractor.py -v
```

### Integration Testing

**CLI Tool**: `scripts/test_extraction.py`

**Test single image**:
```bash
python scripts/test_extraction.py --image tests/SROIE2019/train/img/X00016469622.jpg --verbose
```

**Test batch**:
```bash
python scripts/test_extraction.py --batch tests/SROIE2019/train/img/ --limit 10
```

**Show all candidates**:
```bash
python scripts/test_extraction.py --image receipt.jpg --show-candidates --verbose
```

## Future Improvements

### Phase 5: Confidence Calibration

- Calibrate confidence scores based on validation data
- Learn optimal thresholds for each field
- Adjust scoring weights based on performance

### Phase 6: Adaptive Learning

- Track extraction failures
- Identify common error patterns
- Adjust heuristics based on feedback

### Potential Enhancements

1. **Multi-language Support**: Extend keyword lists for other languages
2. **Custom Field Extraction**: Allow users to define custom fields
3. **Fuzzy Matching**: Handle OCR errors more robustly
4. **Context-Aware Scoring**: Use document structure (tables, sections)
5. **Ensemble Methods**: Combine multiple extraction strategies

## Conclusion

The Field Extraction Engine successfully transforms noisy OCR text into structured data using interpretable heuristic-based methods. The scoring system balances multiple signals to handle real-world receipt variations while maintaining explainability.

**Key Achievements**:
- ✅ Robust multi-field extraction
- ✅ Explainable scoring system
- ✅ Comprehensive edge case handling
- ✅ High-quality test coverage
- ✅ Production-ready CLI tools

**Next Phase**: Confidence calibration and validation on full SROIE dataset.