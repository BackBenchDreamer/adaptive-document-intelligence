"""
Pipeline module for Adaptive Document Intelligence System.

Exports main pipeline classes for document processing.
"""

from pipeline.pipeline import (
    DocumentProcessor,
    BatchProcessor,
    PipelineManager,
    process_image
)

__all__ = [
    'DocumentProcessor',
    'BatchProcessor',
    'PipelineManager',
    'process_image'
]

# Made with Bob
