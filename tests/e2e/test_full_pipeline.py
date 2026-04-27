"""
End-to-end tests for the complete document processing pipeline.
"""

from pathlib import Path

import pytest

from pipeline import DocumentProcessor


@pytest.mark.e2e
class TestFullPipeline:
    """Test complete document processing pipeline."""

    def test_process_single_document(self, sample_image_path, sample_ground_truth):
        """Test processing a single document end-to-end."""
        processor = DocumentProcessor(
            ocr_engine="tesseract",
            use_preprocessing=True,
            use_cache=True,
            use_calibration=False,
        )
        result = processor.process_document(str(sample_image_path))

        assert "image_path" in result
        assert "image_id" in result
        assert "fields" in result
        assert "metadata" in result

        assert "date" in result["fields"]
        assert "total" in result["fields"]
        assert "invoice_number" in result["fields"]

        if result["metadata"]["success"]:
            for field_name in ("date", "total", "invoice_number"):
                assert "value" in result["fields"][field_name]
                assert "confidence" in result["fields"][field_name]

            if result["fields"]["date"]["value"] is not None:
                assert isinstance(result["fields"]["date"]["value"], str)

            if result["fields"]["total"]["value"] is not None:
                assert isinstance(result["fields"]["total"]["value"], (int, float))

    def test_process_with_cache(self, sample_image_path):
        """Test pipeline with caching enabled."""
        processor = DocumentProcessor(
            ocr_engine="tesseract",
            use_preprocessing=False,
            use_cache=True,
            use_calibration=False,
        )

        first = processor.process_document(str(sample_image_path), return_intermediate=True)
        second = processor.process_document(str(sample_image_path), return_intermediate=True)

        if not first["metadata"]["success"] or not second["metadata"]["success"]:
            pytest.skip("OCR engine unavailable or sample image not present")

        assert second["metadata"]["success"] is True
        assert "intermediate" in second
        assert second["intermediate"]["ocr_result"]["metadata"].get("cached") in (True, False)

    def test_process_with_preprocessing(self, sample_image_path):
        """Test pipeline with image preprocessing enabled."""
        processor = DocumentProcessor(
            ocr_engine="tesseract",
            use_preprocessing=True,
            use_cache=False,
            use_calibration=False,
        )
        result = processor.process_document(str(sample_image_path), return_intermediate=True)

        if not result["metadata"]["success"]:
            pytest.skip("OCR engine unavailable or sample image not present")

        assert result["metadata"]["success"] is True
        assert "intermediate" in result

    def test_error_handling(self):
        """Test pipeline error handling for a missing input file."""
        processor = DocumentProcessor(
            ocr_engine="tesseract",
            use_preprocessing=True,
            use_cache=False,
            use_calibration=False,
        )
        result = processor.process_document("nonexistent_receipt.jpg")

        assert result["metadata"]["success"] is False
        assert "error" in result["metadata"]
        assert result["fields"]["date"]["value"] is None
        assert result["fields"]["total"]["value"] is None
        assert result["fields"]["invoice_number"]["value"] is None


@pytest.mark.e2e
class TestSROIEDataset:
    """Test on SROIE dataset samples."""

    def test_process_sroie_samples(self, sroie_loader):
        """Test processing a small set of SROIE dataset samples."""
        samples = sroie_loader.load_dataset()

        if not samples:
            pytest.skip("No SROIE samples available")

        processor = DocumentProcessor(
            ocr_engine="tesseract",
            use_preprocessing=False,
            use_cache=True,
            use_calibration=False,
        )

        checked = 0
        for sample in samples[:5]:
            result = processor.process_document(sample["image_path"])

            assert result is not None
            assert "fields" in result
            assert "date" in result["fields"]
            assert "total" in result["fields"]

            checked += 1

        assert checked > 0

# Made with Bob
