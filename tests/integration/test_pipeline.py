"""
Integration Tests for Pipeline Module

Tests the complete end-to-end pipeline including OCR, extraction,
and confidence scoring working together.

Author: Adaptive Document Intelligence System
Phase: 6 - Pipeline Integration
"""

import pytest
import time
from pathlib import Path
from typing import Dict, List

from pipeline.pipeline import (
    DocumentProcessor,
    BatchProcessor,
    PipelineManager,
    process_image
)
from tests.data.sroie_loader import SROIEDataLoader


class TestDocumentProcessor:
    """Test DocumentProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a processor instance for testing."""
        return DocumentProcessor(
            ocr_engine='tesseract',
            use_cache=True,
            use_calibration=False
        )
    
    @pytest.fixture
    def sample_image(self):
        """Get a sample image path from SROIE dataset."""
        loader = SROIEDataLoader(split='train')
        samples = loader.load_dataset()
        
        # Find a valid sample
        for sample in samples:
            if sample['has_required_fields']:
                return sample['image_path']
        
        pytest.skip("No valid samples found in dataset")
    
    def test_processor_initialization(self, processor):
        """Test processor initializes correctly."""
        assert processor is not None
        assert processor.ocr_engine == 'tesseract'
        assert processor.use_cache is True
        assert processor.use_calibration is False
        assert processor.ocr_manager is not None
        assert processor.extractor is not None
        assert processor.confidence_manager is not None
    
    def test_process_single_document(self, processor, sample_image):
        """Test processing a single document."""
        result = processor.process_document(sample_image)
        
        # Check result structure
        assert 'image_path' in result
        assert 'image_id' in result
        assert 'fields' in result
        assert 'metadata' in result
        
        # Check fields
        assert 'date' in result['fields']
        assert 'total' in result['fields']
        assert 'invoice_number' in result['fields']
        
        # Check each field has required keys
        for field_name in ['date', 'total', 'invoice_number']:
            field = result['fields'][field_name]
            assert 'value' in field
            assert 'confidence' in field
            assert 'raw_value' in field
            assert 0.0 <= field['confidence'] <= 1.0
        
        # Check metadata
        assert 'processing_time' in result['metadata']
        assert 'ocr_engine' in result['metadata']
        assert 'ocr_confidence' in result['metadata']
        assert 'success' in result['metadata']
        assert 'timestamp' in result['metadata']
        
        # Should be successful
        assert result['metadata']['success'] is True
        assert result['metadata']['processing_time'] > 0
    
    def test_process_with_intermediate_results(self, processor, sample_image):
        """Test processing with intermediate results."""
        result = processor.process_document(
            sample_image,
            return_intermediate=True
        )
        
        # Check intermediate results are included
        assert 'intermediate' in result
        assert 'ocr_result' in result['intermediate']
        assert 'extraction_result' in result['intermediate']
        assert 'scored_result' in result['intermediate']
        
        # Check OCR result structure
        ocr_result = result['intermediate']['ocr_result']
        assert 'text' in ocr_result
        assert 'confidence' in ocr_result
        assert 'engine' in ocr_result
    
    def test_process_nonexistent_image(self, processor):
        """Test processing a nonexistent image."""
        result = processor.process_document('nonexistent.jpg')
        
        # Should return error result
        assert result['metadata']['success'] is False
        assert 'error' in result['metadata']
        
        # Fields should be None
        assert result['fields']['date']['value'] is None
        assert result['fields']['total']['value'] is None
        assert result['fields']['invoice_number']['value'] is None
    
    def test_process_batch(self, processor):
        """Test batch processing."""
        # Get a few sample images
        loader = SROIEDataLoader(split='train')
        samples = loader.load_dataset()
        
        # Get first 5 valid samples
        image_paths = []
        for sample in samples:
            if sample['has_required_fields'] and len(image_paths) < 5:
                image_paths.append(sample['image_path'])
        
        if len(image_paths) < 2:
            pytest.skip("Not enough valid samples")
        
        # Process batch
        results = processor.process_batch(image_paths, show_progress=False)
        
        # Check results
        assert len(results) == len(image_paths)
        assert all('image_id' in r for r in results)
        assert all('fields' in r for r in results)
    
    def test_get_statistics(self, processor):
        """Test statistics calculation."""
        # Create some mock results
        results = [
            {
                'image_id': 'test1',
                'fields': {
                    'date': {'value': '2018-03-30', 'confidence': 0.9, 'raw_value': '30/03/2018'},
                    'total': {'value': 10.50, 'confidence': 0.85, 'raw_value': '$10.50'},
                    'invoice_number': {'value': 'INV-001', 'confidence': 0.75, 'raw_value': 'INV-001'}
                },
                'metadata': {
                    'processing_time': 1.0,
                    'success': True
                }
            },
            {
                'image_id': 'test2',
                'fields': {
                    'date': {'value': None, 'confidence': 0.3, 'raw_value': ''},
                    'total': {'value': 20.00, 'confidence': 0.8, 'raw_value': '$20.00'},
                    'invoice_number': {'value': None, 'confidence': 0.2, 'raw_value': ''}
                },
                'metadata': {
                    'processing_time': 1.2,
                    'success': True
                }
            }
        ]
        
        stats = processor.get_statistics(results)
        
        # Check statistics structure
        assert 'total_processed' in stats
        assert 'successful' in stats
        assert 'failed' in stats
        assert 'avg_processing_time' in stats
        assert 'avg_confidence' in stats
        assert 'extraction_rate' in stats
        
        # Check values
        assert stats['total_processed'] == 2
        assert stats['successful'] == 2
        assert stats['failed'] == 0
        assert stats['avg_processing_time'] > 0
        
        # Check field-specific stats
        assert 'date' in stats['avg_confidence']
        assert 'total' in stats['avg_confidence']
        assert 'invoice_number' in stats['avg_confidence']
        
        assert 'date' in stats['extraction_rate']
        assert stats['extraction_rate']['date'] == 0.5  # 1 out of 2
        assert stats['extraction_rate']['total'] == 1.0  # 2 out of 2


class TestBatchProcessor:
    """Test BatchProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a document processor."""
        return DocumentProcessor(ocr_engine='tesseract', use_cache=True)
    
    @pytest.fixture
    def batch_processor(self, processor):
        """Create a batch processor."""
        return BatchProcessor(processor, max_workers=2, use_parallel=False)
    
    def test_batch_processor_initialization(self, batch_processor):
        """Test batch processor initializes correctly."""
        assert batch_processor is not None
        assert batch_processor.processor is not None
        assert batch_processor.max_workers == 2
        assert batch_processor.use_parallel is False
    
    def test_process_directory(self, batch_processor):
        """Test processing a directory."""
        # Use SROIE train directory
        train_dir = Path('tests/SROIE2019/train/img')
        
        if not train_dir.exists():
            pytest.skip("SROIE dataset not found")
        
        # Process first 3 images
        result = batch_processor.process_directory(
            str(train_dir),
            pattern='*.jpg',
            limit=3
        )
        
        # Check result structure
        assert 'results' in result
        assert 'statistics' in result
        assert 'errors' in result
        
        # Check results
        assert len(result['results']) <= 3
        assert isinstance(result['statistics'], dict)
        assert isinstance(result['errors'], list)
    
    def test_process_nonexistent_directory(self, batch_processor):
        """Test processing a nonexistent directory."""
        result = batch_processor.process_directory('nonexistent_dir')
        
        # Should return empty results with error
        assert len(result['results']) == 0
        assert len(result['errors']) > 0


class TestPipelineManager:
    """Test PipelineManager class."""
    
    def test_create_processor_default(self):
        """Test creating processor with default config."""
        processor = PipelineManager.create_processor()
        
        assert processor is not None
        assert processor.ocr_engine == 'tesseract'
        assert processor.use_cache is True
    
    def test_create_processor_custom_config(self):
        """Test creating processor with custom config."""
        config = {
            'ocr_engine': 'tesseract',
            'use_cache': False,
            'use_calibration': True
        }
        
        processor = PipelineManager.create_processor(config)
        
        assert processor.ocr_engine == 'tesseract'
        assert processor.use_cache is False
        assert processor.use_calibration is True
    
    def test_process_sroie_dataset(self):
        """Test processing SROIE dataset."""
        # Process just 2 samples for speed
        result = PipelineManager.process_sroie_dataset(
            split='train',
            limit=2,
            compare_ground_truth=False
        )
        
        # Check result structure
        assert 'results' in result
        assert 'statistics' in result
        assert len(result['results']) <= 2
    
    def test_process_sroie_with_accuracy(self):
        """Test processing SROIE with accuracy calculation."""
        result = PipelineManager.process_sroie_dataset(
            split='train',
            limit=3,
            compare_ground_truth=True
        )
        
        # Check accuracy is included
        assert 'accuracy' in result
        assert 'date' in result['accuracy']
        assert 'total' in result['accuracy']
        assert 'invoice_number' in result['accuracy']
        assert 'overall' in result['accuracy']
        
        # Check accuracy values are valid
        for field, acc in result['accuracy'].items():
            assert 0.0 <= acc <= 1.0
    
    def test_save_results_json(self, tmp_path):
        """Test saving results as JSON."""
        results = [
            {
                'image_id': 'test1',
                'fields': {
                    'date': {'value': '2018-03-30', 'confidence': 0.9, 'raw_value': ''},
                    'total': {'value': 10.50, 'confidence': 0.85, 'raw_value': ''},
                    'invoice_number': {'value': 'INV-001', 'confidence': 0.75, 'raw_value': ''}
                },
                'metadata': {'success': True}
            }
        ]
        
        output_path = tmp_path / 'results.json'
        PipelineManager.save_results(results, str(output_path), format='json')
        
        # Check file was created
        assert output_path.exists()
        
        # Check content
        import json
        with open(output_path) as f:
            loaded = json.load(f)
        
        assert len(loaded) == 1
        assert loaded[0]['image_id'] == 'test1'
    
    def test_save_results_csv(self, tmp_path):
        """Test saving results as CSV."""
        results = [
            {
                'image_id': 'test1',
                'fields': {
                    'date': {'value': '2018-03-30', 'confidence': 0.9, 'raw_value': ''},
                    'total': {'value': 10.50, 'confidence': 0.85, 'raw_value': ''},
                    'invoice_number': {'value': 'INV-001', 'confidence': 0.75, 'raw_value': ''}
                },
                'metadata': {'processing_time': 1.0, 'success': True}
            }
        ]
        
        output_path = tmp_path / 'results.csv'
        PipelineManager.save_results(results, str(output_path), format='csv')
        
        # Check file was created
        assert output_path.exists()
        
        # Check content
        import csv
        with open(output_path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        assert len(rows) == 2  # Header + 1 data row
        assert rows[0][0] == 'image_id'
        assert rows[1][0] == 'test1'


class TestConvenienceFunction:
    """Test convenience function."""
    
    def test_process_image_function(self):
        """Test the process_image convenience function."""
        # Get a sample image
        loader = SROIEDataLoader(split='train')
        samples = loader.load_dataset()
        
        # Find a valid sample
        sample_image = None
        for sample in samples:
            if sample['has_required_fields']:
                sample_image = sample['image_path']
                break
        
        if not sample_image:
            pytest.skip("No valid samples found")
        
        # Process using convenience function
        result = process_image(sample_image, ocr_engine='tesseract')
        
        # Check result
        assert result is not None
        assert 'fields' in result
        assert 'metadata' in result
        assert result['metadata']['success'] is True


class TestEndToEndIntegration:
    """Test complete end-to-end integration."""
    
    def test_full_pipeline_flow(self):
        """Test the complete pipeline from image to structured output."""
        # Get a sample
        loader = SROIEDataLoader(split='train')
        samples = loader.load_dataset()
        
        sample = None
        for s in samples:
            if s['has_required_fields']:
                sample = s
                break
        
        if not sample:
            pytest.skip("No valid samples found")
        
        # Create processor
        processor = DocumentProcessor(
            ocr_engine='tesseract',
            use_cache=True,
            use_calibration=False
        )
        
        # Process document
        start_time = time.time()
        result = processor.process_document(
            sample['image_path'],
            return_intermediate=True
        )
        processing_time = time.time() - start_time
        
        # Verify complete pipeline execution
        assert result['metadata']['success'] is True
        assert processing_time < 10.0  # Should complete in reasonable time
        
        # Verify all stages executed
        assert 'intermediate' in result
        assert result['intermediate']['ocr_result']['text']  # OCR produced text
        assert 'date' in result['intermediate']['extraction_result']  # Extraction ran
        assert 'date' in result['intermediate']['scored_result']  # Scoring ran
        
        # Verify final output quality
        fields = result['fields']
        
        # At least one field should be extracted
        extracted_count = sum(
            1 for field in fields.values()
            if field['value'] is not None
        )
        assert extracted_count > 0, "Pipeline should extract at least one field"
        
        # Confidence scores should be reasonable
        for field_name, field_data in fields.items():
            if field_data['value'] is not None:
                assert 0.0 <= field_data['confidence'] <= 1.0
                # High-confidence extractions should have confidence > 0.5
                if field_data['confidence'] > 0.7:
                    assert field_data['value'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

# Made with Bob
