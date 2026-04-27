# Phase 8: Error Analysis System

## 1. Error Analysis Overview

The Phase 8 error analysis system explains *why* the Adaptive Document Intelligence System fails on specific samples. Instead of only reporting aggregate accuracy, it classifies failures into deterministic categories, summarizes their distribution, surfaces representative examples, and generates actionable recommendations.

The module is centered on three responsibilities:

- **Error categorization**: Assign each failed extraction to a reason such as subtotal confusion, OCR noise, or date parsing error.
- **Pattern detection**: Identify recurring dataset-wide trends such as low OCR quality correlation or repeated OCR confusion pairs.
- **Reporting**: Produce machine-readable and human-readable summaries for debugging and prioritization.

Primary implementation files:

```text
tests/analysis/error_analysis.py
scripts/run_error_analysis.py
tests/metrics/evaluation.py
```

## 2. Error Categories

The system uses the following `ErrorType` categories.

### `wrong_total`
Used when a total value is extracted but does not match the ground truth and does not strongly look like a subtotal-specific error.

Typical causes:
- Wrong numeric candidate chosen
- Incorrect total heuristic
- Tax or discount amount selected incorrectly

### `subtotal_confusion`
Used when the predicted amount appears to be a subtotal, pre-tax amount, or non-final amount instead of the true final total.

Typical indicators:
- Predicted amount appears near `subtotal`-like keywords
- Ground truth total appears near `total`-like keywords
- Tax/discount lines exist and predicted amount is lower than the final total

### `date_parsing_error`
Used when a date-like value is extracted but cannot be reliably parsed into the expected normalized form.

Typical causes:
- Unsupported date pattern
- OCR-distorted digits
- Non-standard separators

### `date_format_error`
Used when a date is extracted but normalized incorrectly, or when the selected date differs from the intended one because of formatting or ambiguity.

Typical causes:
- Wrong day/month ordering
- Multiple candidate dates present
- Selection of issue date instead of transaction date

### `ocr_noise`
Used when OCR quality or character confusions likely caused the extraction failure.

Typical indicators:
- `0/O`, `1/I`, `5/S`, `8/B` confusions
- Corrupted punctuation or symbol bursts
- Heavily degraded OCR text

### `missing_field`
Used when no usable value is extracted for a required field.

Typical causes:
- OCR missed the relevant region
- Extraction rules were too strict
- Field absent from OCR text

### `extraction_failure`
Used when the system cannot reliably identify the intended field in OCR output, even if some relevant content may exist.

Typical causes:
- Layout ambiguity
- Candidate scoring failure
- Missing final total line in OCR text

### `low_confidence`
Used when the prediction is already low-confidence and incorrect, indicating uncertainty was correctly signaled but unresolved.

Typical value:
- Confidence below `0.5`

### `other`
Fallback category for deterministic but uncategorized failures.

## 3. Pattern Detection

The `FailurePatternDetector` identifies systematic dataset-level issues from categorized errors.

### OCR quality correlation
A simple OCR quality estimate is derived from:
- alphanumeric ratio
- unusual symbol ratio
- repeated punctuation/noise penalty

This helps compare failure concentration between lower- and higher-quality OCR outputs.

### Confidence correlation
Errors are split into low-confidence and high-confidence groups to estimate whether confidence is informative.

This is useful for:
- rejection-threshold decisions
- manual review policies
- calibration follow-up

### Field-specific patterns

#### Date-specific
The detector looks for:
- failed format families such as `DD/MM/YYYY`, `DD-MM-YYYY`, or textual month formats
- OCR confusion pairs in failed date strings

#### Total-specific
The detector looks for:
- subtotal confusion rate among total errors
- possible bottom-of-document or final-total selection issues

### OCR confusion patterns
Common OCR confusion pairs are counted, such as:
- `0 ↔ O`
- `1 ↔ I`
- `5 ↔ S`
- `8 ↔ B`

These patterns help prioritize OCR cleanup and parser robustness work.

## 4. Usage Examples

### Basic analysis
```bash
python scripts/run_error_analysis.py --split train
```

### Analyze a subset
```bash
python scripts/run_error_analysis.py --split train --limit 50
```

### Show examples
```bash
python scripts/run_error_analysis.py --split train --show-examples --limit 10
```

### Focus on one category
```bash
python scripts/run_error_analysis.py --split train --error-type subtotal_confusion
```

### Save JSON report
```bash
python scripts/run_error_analysis.py --split train --output output/error_report.json
```

### Generate HTML report
```bash
python scripts/run_error_analysis.py --split train --output output/error_report.json --generate-report
```

### Disable OCR cache
```bash
python scripts/run_error_analysis.py --split train --no-cache
```

## 5. Interpreting Results

A typical report contains the following sections.

### Summary
Provides:
- total samples analyzed
- total field-level errors
- overall error rate
- per-field error rates for `date` and `total`

### By category
Shows:
- category count
- percentage of all errors
- dominant field
- representative examples

Interpretation guideline:
- high `subtotal_confusion` means total-selection heuristics need work
- high `date_parsing_error` means parser coverage is insufficient
- high `ocr_noise` means OCR cleanup or preprocessing matters

### Patterns
Shows:
- OCR quality correlation
- confidence correlation
- field-specific recurring issues
- OCR confusion pairs

Interpretation guideline:
- if low-quality OCR dominates, preprocessing should be prioritized
- if low-confidence errors dominate, thresholding may help
- if one date format dominates failures, targeted parser support is justified

### Insights
Insights are short, actionable statements automatically generated from the largest failure categories and strongest correlations.

Example:
- `28.6% of errors are subtotal confusion - improve total detection heuristics`

### Recommendations
Recommendations translate failure patterns into concrete engineering next steps.

Example:
- `Add stronger penalties for 'subtotal' keyword proximity in total extraction`

## 6. Actionable Insights

Use the analysis output to prioritize improvements.

### If subtotal confusion is dominant
Action ideas:
- increase penalties for subtotal keywords
- prefer final/bottom-most total candidates
- use stronger tax/discount-aware scoring

### If date parsing errors are dominant
Action ideas:
- add more date patterns
- detect format family before normalization
- separate OCR cleanup from date parsing

### If OCR noise is dominant
Action ideas:
- preprocess low-quality images
- normalize OCR text before extraction
- add OCR confusion-tolerant parsing for dates and totals

### If low-confidence errors are frequent
Action ideas:
- reject predictions below a threshold
- route low-confidence cases to human review
- analyze confidence calibration further

## 7. Known Limitations

1. **Heuristic categorization**  
   Error categories are rule-based and may not perfectly reflect the root cause.

2. **OCR quality estimate is approximate**  
   Quality is inferred from text characteristics rather than image-level quality metrics.

3. **Field scope is limited**  
   The current analysis focuses on `date` and `total`, matching the evaluation scope.

4. **No automatic fixes**  
   This phase only analyzes failures and does not modify extraction behavior.

5. **Single-pass explanations**  
   Explanations are concise and deterministic rather than model-generated or interactive.

6. **Report quality depends on OCR text availability**  
   Missing intermediate OCR text reduces explanation quality.

## 8. Troubleshooting

### Problem: CLI fails with import errors
Ensure the command is run from the project root:

```bash
cd /Users/jeyadheepv/grepo/adaptive-document-intelligence
python scripts/run_error_analysis.py --split train
```

### Problem: OCR text is empty in the report
Cause:
- processor did not return intermediate OCR results
- OCR stage failed for those documents

Check:
- `DocumentEvaluator.evaluate_with_error_tracking()`
- OCR cache validity
- OCR engine availability

### Problem: Too many `other` errors
Cause:
- current heuristics are not specific enough for those failures

Action:
- inspect examples in the `other` category
- add a new category or refine existing rules

### Problem: Error rates look too high
Possible causes:
- field-level error rate is being interpreted as document-level rate
- OCR cache contains stale results
- pipeline extraction schema changed

Action:
- compare `evaluation` and `summary` sections in the output
- rerun with `--no-cache`
- verify `DocumentProcessor` output schema

### Problem: HTML report not created
If `--generate-report` is used without `--output`, the default output is:

```text
output/error_report.html
```

If `--output output/error_report.json` is used, the HTML file is created as:

```text
output/error_report.html
```

## Programmatic Example

```python
from pipeline.pipeline import DocumentProcessor
from tests.metrics.evaluation import DocumentEvaluator
from tests.analysis.error_analysis import ErrorAnalyzer

processor = DocumentProcessor(use_cache=True)
evaluator = DocumentEvaluator(processor)
analyzer = ErrorAnalyzer()

evaluation_results, error_records = evaluator.evaluate_with_error_tracking(
    split="train",
    limit=100
)

grouped_predictions = {}
grouped_truth = {}
grouped_ocr = {}

for record in error_records:
    image_id = record["image_id"]
    grouped_predictions.setdefault(image_id, {"image_id": image_id})
    grouped_truth.setdefault(image_id, {"image_id": image_id})
    grouped_ocr.setdefault(image_id, record["ocr_text"])

    field = record["field_name"]
    grouped_predictions[image_id][field] = record["prediction"]
    grouped_predictions[image_id][f"{field}_confidence"] = record["confidence"]
    grouped_truth[image_id][field] = record["ground_truth"]

predictions = [grouped_predictions[key] for key in sorted(grouped_predictions)]
ground_truth = [grouped_truth[key] for key in sorted(grouped_truth)]
ocr_results = [grouped_ocr[key] for key in sorted(grouped_ocr)]

report = analyzer.analyze_errors(predictions, ground_truth, ocr_results)
print(report["insights"])
```

## Output Structure

The main report format is:

```python
{
    "summary": {...},
    "by_category": {...},
    "patterns": {...},
    "insights": [...],
    "recommendations": [...],
    "errors": [...],
    "evaluation": {...},  # added by CLI
}
```

## Made with Bob