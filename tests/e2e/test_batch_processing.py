"""
End-to-end tests for batch processing capabilities.
"""

import pytest

from pipeline import BatchProcessor, DocumentProcessor


@pytest.mark.e2e
class TestBatchProcessing:
    """Test batch document processing."""

    def test_batch_process_multiple_documents(self, sroie_loader):
        """Test processing multiple documents in a batch."""
        samples = sroie_loader.load_dataset()
        if len(samples) < 2:
            pytest.skip("Not enough SROIE samples available")

        image_paths = [sample["image_path"] for sample in samples[:3]]
        processor = DocumentProcessor(
            ocr_engine="tesseract",
            use_preprocessing=False,
            use_cache=True,
            use_calibration=False,
        )
        results = processor.process_batch(image_paths, show_progress=False)

        assert len(results) == len(image_paths)
        assert all("fields" in result for result in results)
        assert all("metadata" in result for result in results)

    def test_batch_process_with_parallel(self, sroie_loader):
        """Test parallel batch processing."""
        samples = sroie_loader.load_dataset()
        if len(samples) < 2:
            pytest.skip("Not enough SROIE samples available")

        image_paths = [sample["image_path"] for sample in samples[:3]]
        processor = DocumentProcessor(
            ocr_engine="tesseract",
            use_preprocessing=False,
            use_cache=True,
            use_calibration=False,
        )
        batch_processor = BatchProcessor(processor, max_workers=2, use_parallel=True)
        results = batch_processor._process_parallel(image_paths=[__import__("pathlib").Path(p) for p in image_paths])

        assert len(results) == len(image_paths)
        assert all("image_id" in result for result in results)

    def test_batch_process_error_recovery(self):
        """Test batch processing continues after errors."""
        processor = DocumentProcessor(
            ocr_engine="tesseract",
            use_preprocessing=False,
            use_cache=False,
            use_calibration=False,
        )
        image_paths = ["missing_one.jpg", "missing_two.jpg"]

        results = processor.process_batch(image_paths, show_progress=False)

        assert len(results) == 2
        assert all(result["metadata"]["success"] is False for result in results)

    def test_batch_process_progress_tracking(self, sroie_loader):
        """Test statistics/progress style output from directory batch processing."""
        samples = sroie_loader.load_dataset()
        if not samples:
            pytest.skip("No SROIE samples available")

        processor = DocumentProcessor(
            ocr_engine="tesseract",
            use_preprocessing=False,
            use_cache=True,
            use_calibration=False,
        )
        batch_processor = BatchProcessor(processor, max_workers=2, use_parallel=False)
        first_image_dir = __import__("pathlib").Path(samples[0]["image_path"]).parent

        result = batch_processor.process_directory(str(first_image_dir), pattern="*.jpg", limit=2)

        assert "results" in result
        assert "statistics" in result
        assert "errors" in result

# Made with Bob
