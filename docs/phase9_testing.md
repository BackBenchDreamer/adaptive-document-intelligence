# Phase 9: Testing Framework

## 1. Testing Overview

The Adaptive Document Intelligence System uses a layered testing strategy:

- **Unit tests** validate isolated components such as OCR helpers, extraction logic, confidence scoring, and utility functions.
- **Integration tests** validate component boundaries, such as OCR feeding extraction and extraction feeding confidence scoring.
- **End-to-end tests** validate complete workflows, including single-document processing and batch execution.

Testing is designed around these principles:

- Preserve existing working tests.
- Add coverage for missing areas rather than duplicating behavior.
- Keep most tests fast and deterministic.
- Mark broader workflow tests clearly using pytest markers.
- Allow graceful skipping when OCR engines or sample assets are unavailable.

## 2. Test Structure

The test suite is organized as follows:

```text
tests/
├── __init__.py
├── conftest.py
├── data/
│   ├── __init__.py
│   ├── sroie_loader.py
│   └── test_sroie_loader.py
├── unit/
│   ├── __init__.py
│   ├── test_ocr.py
│   ├── test_extractor.py
│   ├── test_confidence.py
│   ├── test_evaluation.py
│   ├── test_error_analysis.py
│   └── test_utils.py
├── integration/
│   ├── __init__.py
│   ├── test_pipeline.py
│   ├── test_ocr_extraction.py
│   └── test_extraction_confidence.py
├── e2e/
│   ├── __init__.py
│   ├── test_full_pipeline.py
│   └── test_batch_processing.py
├── fixtures/
│   └── __init__.py
└── run_tests.py
```

## 3. Running Tests

### Run all tests

```bash
python tests/run_tests.py
```

### Run only unit tests

```bash
python tests/run_tests.py unit
```

### Run only integration tests

```bash
python tests/run_tests.py integration
```

### Run only end-to-end tests

```bash
python tests/run_tests.py e2e
```

### Run with coverage

```bash
python tests/run_tests.py coverage
```

### Run a specific file

```bash
pytest tests/unit/test_extractor.py -v
```

### Run a specific class

```bash
pytest tests/unit/test_extractor.py::TestDateExtractor -v
```

### Run a specific test

```bash
pytest tests/unit/test_extractor.py::TestDateExtractor::test_extract_date_dd_mm_yyyy -v
```

### Run tests matching a keyword

```bash
pytest -k "date" -v
```

### Run tests by marker

```bash
pytest -m "unit" -v
pytest -m "integration" -v
pytest -m "e2e" -v
pytest -m "not slow" -v
```

## 4. Writing Tests

When adding tests:

- Prefer **unit tests first** for pure logic.
- Use **integration tests** for component interaction contracts.
- Use **e2e tests** only for full workflow validation.
- Assert on:
  - output structure
  - key field presence
  - confidence bounds
  - error handling behavior
- Avoid brittle OCR content assertions unless the asset and OCR environment are stable.
- Skip tests gracefully when optional OCR dependencies or dataset images are unavailable.

Recommended conventions:

- Name files as `test_<feature>.py`
- Name classes as `Test<Feature>`
- Name methods/functions as `test_<behavior>`
- Keep one behavioral concern per test

## 5. Test Fixtures

Shared fixtures are defined in `tests/conftest.py`.

Available fixtures include:

- `test_data_dir`: path to the test fixtures directory
- `sample_image_path`: dataset-backed sample image path
- `sample_ocr_text`: clean OCR-like sample text
- `poor_quality_ocr_text`: noisy OCR-like sample text
- `sample_ground_truth`: expected structured values
- `ocr_manager`: shared OCR manager instance
- `document_processor`: shared pipeline processor instance
- `sroie_loader`: dataset loader for SROIE-backed tests

Example usage:

```python
def test_total_extraction(sample_ocr_text):
    assert "Total" in sample_ocr_text
```

## 6. Coverage Reports

Coverage is generated with:

```bash
python tests/run_tests.py coverage
```

This produces:

- terminal coverage summary
- HTML report via `htmlcov/index.html`

Coverage configuration is defined in `.coveragerc`.

Interpretation guidelines:

- Low coverage in a core module usually indicates missing behavioral tests.
- Focus first on:
  - extraction edge cases
  - pipeline error paths
  - confidence scoring branches
  - utility helper behavior

## 7. Continuous Integration

Optional CI/CD integration should run:

1. dependency installation
2. unit tests
3. integration tests
4. optional coverage reporting

Suggested CI order:

```bash
pip install -r requirements.txt
python tests/run_tests.py unit
python tests/run_tests.py integration
python tests/run_tests.py coverage
```

E2E tests may be separated if OCR engines or dataset assets are not guaranteed in the CI environment.

## 8. Troubleshooting

### `pytest` import cannot be resolved
Install dependencies:

```bash
pip install -r requirements.txt
```

### OCR tests fail or skip
Ensure system OCR dependencies are installed:

- macOS: `brew install tesseract`
- PaddleOCR requires Python package support and its runtime dependencies

### Dataset-backed tests skip
Some tests rely on SROIE samples being present under `tests/SROIE2019/`.

### Coverage command fails
Make sure `pytest-cov` is installed:

```bash
pip install pytest-cov
```

### End-to-end tests are slow
Use markers to narrow scope:

```bash
pytest -m "not e2e" -v
```

## 9. Notes

This phase extends the existing test base by:

- preserving previous unit and integration suites
- adding utility coverage
- adding extraction/confidence integration checks
- adding full-pipeline and batch-processing e2e validation
- adding a standardized test runner and configuration