"""
Core module for Adaptive Document Intelligence.

This module provides core functionality including:
- Configuration management
- Logging infrastructure
- Utility functions
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .config import Config
from .logging_config import setup_logging
from .utils import (
    ensure_dir,
    load_json,
    save_json,
    get_file_hash,
    format_confidence,
)

__all__ = [
    "Config",
    "setup_logging",
    "ensure_dir",
    "load_json",
    "save_json",
    "get_file_hash",
    "format_confidence",
]

# Made with Bob
