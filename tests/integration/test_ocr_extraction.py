"""
Integration tests for OCR and extraction working together.
"""

import pytest

from pipeline.extractor import DateExtractor, ExtractionManager, TotalExtractor
from pipeline.ocr import OCRManager


@pytest.mark.integration
class TestOCRExtractionIntegration:
    """Test OCR and extraction working together."""

    def test_ocr_to_date_extraction(self, sample_image_path):
        """Test OCR output feeds into date extraction."""
        ocr_manager = OCRManager(preferred_engine="tesseract", enable_cache=True)
        ocr_result = ocr_manager.extract_text(str(sample_image_path))

        if not ocr_result["text"]:
            pytest.skip("OCR engine unavailable or sample image not present")

        extractor = DateExtractor()
        date_result = extractor.extract(ocr_result["text"])

        assert date_result is not None
        assert "value" in date_result
        assert "confidence" in date_result
        assert 0.0 <= date_result["confidence"] <= 1.0

    def test_ocr_to_total_extraction(self, sample_image_path):
        """Test OCR output feeds into total extraction."""
        ocr_manager = OCRManager(preferred_engine="tesseract", enable_cache=True)
        ocr_result = ocr_manager.extract_text(str(sample_image_path))

        if not ocr_result["text"]:
            pytest.skip("OCR engine unavailable or sample image not present")

        extractor = TotalExtractor()
        total_result = extractor.extract(ocr_result["text"])

        assert total_result is not None
        assert "value" in total_result
        assert "confidence" in total_result
        assert 0.0 <= total_result["confidence"] <= 1.0

    def test_extraction_manager_consumes_ocr_output(self, sample_image_path):
        """Test the extraction manager accepts real OCR output structure."""
        ocr_manager = OCRManager(preferred_engine="tesseract", enable_cache=True)
        ocr_result = ocr_manager.extract_text(str(sample_image_path))

        if not ocr_result["text"]:
            pytest.skip("OCR engine unavailable or sample image not present")

        manager = ExtractionManager()
        extraction_result = manager.extract_fields(ocr_result)

        assert "date" in extraction_result
        assert "total" in extraction_result
        assert "invoice_number" in extraction_result
        assert "metadata" in extraction_result

    def test_poor_ocr_quality_handling(self, poor_quality_ocr_text):
        """Test extraction handles poor OCR quality text gracefully."""
        manager = ExtractionManager()
        extraction_result = manager.extract_fields(
            {
                "text": poor_quality_ocr_text,
                "confidence": 0.35,
                "metadata": {"engine": "mock"},
            }
        )

        assert extraction_result is not None
        assert "date" in extraction_result
        assert "total" in extraction_result
        assert "metadata" in extraction_result
        assert extraction_result["metadata"]["ocr_confidence"] == 0.35

# Made with Bob
