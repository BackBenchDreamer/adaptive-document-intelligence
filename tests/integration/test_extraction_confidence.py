"""
Integration tests for extraction and confidence scoring.
"""

import pytest

from pipeline.confidence import ConfidenceManager
from pipeline.extractor import ExtractionManager


@pytest.mark.integration
class TestExtractionConfidenceIntegration:
    """Test extraction and confidence scoring together."""

    def test_high_quality_extraction_confidence(self, sample_ocr_text):
        """Test confidence scoring for a high-quality extraction."""
        extraction_manager = ExtractionManager()
        confidence_manager = ConfidenceManager(use_calibration=False)

        ocr_result = {
            "text": sample_ocr_text,
            "confidence": 0.95,
            "engine": "mock",
            "metadata": {},
        }
        extraction_result = extraction_manager.extract_fields(ocr_result)
        scored_result = confidence_manager.score_extraction(extraction_result, ocr_result)

        assert "date" in scored_result
        assert "total" in scored_result
        assert scored_result["date"]["confidence"] > 0.5
        assert scored_result["total"]["confidence"] > 0.5

    def test_low_quality_extraction_confidence(self, poor_quality_ocr_text):
        """Test confidence scoring for low-quality OCR input."""
        extraction_manager = ExtractionManager()
        confidence_manager = ConfidenceManager(use_calibration=False)

        ocr_result = {
            "text": poor_quality_ocr_text,
            "confidence": 0.25,
            "engine": "mock",
            "metadata": {},
        }
        extraction_result = extraction_manager.extract_fields(ocr_result)
        scored_result = confidence_manager.score_extraction(extraction_result, ocr_result)

        assert "metadata" in scored_result
        for field_name in ("date", "total", "invoice_number"):
            if field_name in scored_result:
                assert 0.0 <= scored_result[field_name]["confidence"] <= 1.0

    def test_missing_field_confidence(self):
        """Test confidence behavior when a field is missing."""
        confidence_manager = ConfidenceManager(use_calibration=False)

        extraction_result = {
            "date": {"value": None, "confidence": 0.0, "raw_value": ""},
            "total": {"value": 28.05, "confidence": 0.8, "raw_value": "$28.05"},
        }
        ocr_result = {"text": "Total: $28.05", "confidence": 0.9, "metadata": {}}
        scored_result = confidence_manager.score_extraction(extraction_result, ocr_result)

        assert scored_result["date"]["value"] is None
        assert scored_result["date"]["confidence"] >= 0.0
        assert scored_result["total"]["value"] == 28.05
        assert scored_result["total"]["confidence"] > scored_result["date"]["confidence"]

# Made with Bob
