"""
OCR Module for Adaptive Document Intelligence System.

This module provides OCR functionality with:
- Tesseract OCR (REQUIRED, default)
- PaddleOCR (OPTIONAL, fallback)
- Preprocessing and caching support

Author: Adaptive Document Intelligence System
Phase: 3 - OCR Integration
"""

import os
import logging
import hashlib
from pathlib import Path
from typing import Dict, Optional, Any
import time

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    from paddleocr import PaddleOCR
    HAS_PADDLEOCR = True
except ImportError:
    HAS_PADDLEOCR = False

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class OCREngine:
    """Base class for OCR engines."""
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            {
                'text': str,
                'confidence': float,
                'engine': str,
                'metadata': dict
            }
        """
        raise NotImplementedError


class TesseractEngine(OCREngine):
    """Tesseract OCR engine (REQUIRED, default)."""
    
    def __init__(self):
        """Initialize Tesseract engine with robust path detection."""
        if not HAS_TESSERACT:
            raise ImportError(
                "pytesseract Python package is NOT installed.\n"
                "Install with: pip install pytesseract>=0.3.10\n"
                "Or: pip3 install --break-system-packages pytesseract>=0.3.10"
            )
        
        # STEP 1: Explicit path resolution with priority order
        resolved_path = None
        detection_log = []
        
        # Priority 1: Environment variable
        env_path = os.getenv('TESSERACT_CMD')
        if env_path:
            if os.path.isfile(env_path):
                resolved_path = env_path
                detection_log.append(f"✓ Found via TESSERACT_CMD: {env_path}")
            else:
                detection_log.append(f"✗ TESSERACT_CMD set but file not found: {env_path}")
        
        # Priority 2: Common paths (if not found via env var)
        if not resolved_path:
            common_paths = [
                '/opt/homebrew/bin/tesseract',  # macOS Homebrew (Apple Silicon) - CONFIRMED
                '/usr/local/bin/tesseract',      # macOS Homebrew (Intel)
                '/usr/bin/tesseract',            # Linux standard
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # Windows
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            
            for path in common_paths:
                if os.path.isfile(path):
                    resolved_path = path
                    detection_log.append(f"✓ Found at common path: {path}")
                    break
                else:
                    detection_log.append(f"✗ Not found: {path}")
        
        # Set the resolved path
        if resolved_path:
            pytesseract.pytesseract.tesseract_cmd = resolved_path
            logger.info(f"Tesseract binary set to: {resolved_path}")
        else:
            detection_log.append("⚠ Using default system PATH")
            logger.info("Using default Tesseract path (system PATH)")
        
        # STEP 2: Immediate validation after setting path
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"✓ Tesseract OCR initialized successfully (version: {version})")
            logger.debug("Path detection log:\n" + "\n".join(detection_log))
        except pytesseract.TesseractNotFoundError as e:
            # Tesseract binary not found at any location
            logger.error("Tesseract binary NOT FOUND at any known location")
            logger.error("Path detection log:\n" + "\n".join(detection_log))
            raise RuntimeError(
                "❌ Tesseract binary NOT FOUND at any known location.\n\n"
                "INSTALLATION REQUIRED:\n"
                "  • macOS:          brew install tesseract\n"
                "  • Ubuntu/Debian:  sudo apt-get install tesseract-ocr\n"
                "  • Windows:        Download from https://github.com/UB-Mannheim/tesseract/wiki\n\n"
                "If already installed, set environment variable:\n"
                "  export TESSERACT_CMD=/path/to/tesseract\n\n"
                f"Paths checked:\n" + "\n".join(detection_log) + f"\n\nOriginal error: {e}"
            )
        except Exception as e:
            # Tesseract binary found but failed to execute
            logger.error(f"Tesseract binary found but FAILED to execute: {e}")
            logger.error("Path detection log:\n" + "\n".join(detection_log))
            raise RuntimeError(
                f"❌ Tesseract binary found at '{resolved_path or 'system PATH'}' but FAILED to execute.\n\n"
                "POSSIBLE CAUSES:\n"
                "  • Binary is corrupted or incompatible\n"
                "  • Missing dependencies\n"
                "  • Permission issues\n\n"
                "Try reinstalling Tesseract:\n"
                "  • macOS:          brew reinstall tesseract\n"
                "  • Ubuntu/Debian:  sudo apt-get install --reinstall tesseract-ocr\n\n"
                f"Paths checked:\n" + "\n".join(detection_log) + f"\n\nOriginal error: {e}"
            )
    
    def _detect_tesseract_path(self) -> Optional[str]:
        """
        Detect Tesseract binary path across different platforms.
        
        Priority:
        1. TESSERACT_CMD environment variable
        2. Common installation paths
        3. System PATH (default pytesseract behavior)
        
        Returns:
            Path to tesseract binary or None to use default
        """
        # 1. Check environment variable first
        env_path = os.getenv('TESSERACT_CMD')
        if env_path and os.path.isfile(env_path):
            logger.info(f"Found Tesseract via TESSERACT_CMD: {env_path}")
            return env_path
        
        # 2. Check common installation paths
        common_paths = [
            # macOS (Apple Silicon - Homebrew)
            '/opt/homebrew/bin/tesseract',
            # macOS (Intel - Homebrew)
            '/usr/local/bin/tesseract',
            # Linux (standard)
            '/usr/bin/tesseract',
            # Windows (common installation)
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        
        for path in common_paths:
            if os.path.isfile(path):
                logger.info(f"Found Tesseract at common path: {path}")
                return path
        
        # 3. Return None to use default pytesseract behavior (checks system PATH)
        logger.info("Using default Tesseract path (system PATH)")
        return None
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text using Tesseract."""
        start_time = time.time()
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Extract text with detailed data
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                lang='eng'
            )
            
            # Combine text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if conf > 0:  # Valid confidence
                    text = data['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        confidences.append(conf / 100.0)  # Normalize to [0, 1]
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"Tesseract extracted {len(full_text)} chars "
                f"(confidence: {avg_confidence:.2f}, time: {processing_time:.2f}s)"
            )
            
            return {
                'text': full_text,
                'confidence': avg_confidence,
                'engine': 'tesseract',
                'metadata': {
                    'processing_time': processing_time,
                    'num_words': len(text_parts),
                    'image_path': str(image_path)
                }
            }
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'engine': 'tesseract',
                'metadata': {
                    'error': str(e),
                    'processing_time': time.time() - start_time
                }
            }


class PaddleOCREngine(OCREngine):
    """PaddleOCR engine (OPTIONAL, fallback)."""
    
    def __init__(self, use_gpu: bool = False):
        """Initialize PaddleOCR engine."""
        if not HAS_PADDLEOCR:
            raise ImportError(
                "PaddleOCR not installed. This is OPTIONAL. "
                "Install with: pip install paddlepaddle paddleocr"
            )
        
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                use_gpu=use_gpu,
                show_log=False
            )
            logger.info(f"PaddleOCR initialized (GPU: {use_gpu})")
        except Exception as e:
            logger.error(f"PaddleOCR initialization failed: {e}")
            raise
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text using PaddleOCR."""
        start_time = time.time()
        
        try:
            # Run OCR
            result = self.ocr.ocr(str(image_path), cls=True)
            
            # Extract text and confidence
            text_parts = []
            confidences = []
            
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        text = line[1][0]
                        conf = line[1][1]
                        text_parts.append(text)
                        confidences.append(conf)
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"PaddleOCR extracted {len(full_text)} chars "
                f"(confidence: {avg_confidence:.2f}, time: {processing_time:.2f}s)"
            )
            
            return {
                'text': full_text,
                'confidence': avg_confidence,
                'engine': 'paddleocr',
                'metadata': {
                    'processing_time': processing_time,
                    'num_lines': len(text_parts),
                    'image_path': str(image_path)
                }
            }
            
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'engine': 'paddleocr',
                'metadata': {
                    'error': str(e),
                    'processing_time': time.time() - start_time
                }
            }


class OCRManager:
    """
    Manages OCR engines with fallback support.
    
    Priority:
    1. Tesseract (REQUIRED, default)
    2. PaddleOCR (OPTIONAL, fallback if Tesseract fails)
    """
    
    def __init__(
        self,
        preferred_engine: str = 'tesseract',
        enable_cache: bool = True,
        cache_dir: str = 'output/cache/ocr'
    ):
        """
        Initialize OCR manager.
        
        Args:
            preferred_engine: 'tesseract' or 'paddleocr'
            enable_cache: Enable result caching
            cache_dir: Cache directory path
        """
        self.preferred_engine = preferred_engine
        self.enable_cache = enable_cache
        self.cache_dir = Path(cache_dir)
        
        if enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize engines
        self.engines = {}
        
        # Always try to initialize Tesseract (REQUIRED)
        try:
            self.engines['tesseract'] = TesseractEngine()
            logger.info("Tesseract engine loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Tesseract (REQUIRED): {e}")
            raise RuntimeError(
                "Tesseract OCR is REQUIRED but failed to initialize. "
                "Please install Tesseract OCR on your system."
            )
        
        # Optionally try to initialize PaddleOCR
        if HAS_PADDLEOCR:
            try:
                self.engines['paddleocr'] = PaddleOCREngine()
                logger.info("PaddleOCR engine loaded successfully (optional)")
            except Exception as e:
                logger.warning(f"PaddleOCR not available (optional): {e}")
        
        # Validate preferred engine
        if preferred_engine not in self.engines:
            logger.warning(
                f"Preferred engine '{preferred_engine}' not available, "
                f"falling back to tesseract"
            )
            self.preferred_engine = 'tesseract'
        
        logger.info(
            f"OCRManager initialized (preferred: {self.preferred_engine}, "
            f"available: {list(self.engines.keys())})"
        )
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from image with fallback support.
        
        Args:
            image_path: Path to image file
            
        Returns:
            OCR result dictionary
        """
        image_path = str(image_path)
        
        # Check cache
        if self.enable_cache:
            cached_result = self._get_cached_result(image_path)
            if cached_result:
                logger.debug(f"Using cached OCR result for {image_path}")
                return cached_result
        
        # Try preferred engine
        result = None
        engine = self.engines.get(self.preferred_engine)
        
        if engine:
            logger.info(f"Extracting text with {self.preferred_engine}")
            result = engine.extract_text(image_path)
            
            # Check if extraction was successful
            if result and result.get('text'):
                if self.enable_cache:
                    self._cache_result(image_path, result)
                return result
        
        # Fallback to other engines
        for engine_name, engine in self.engines.items():
            if engine_name == self.preferred_engine:
                continue
            
            logger.warning(
                f"Preferred engine failed, trying fallback: {engine_name}"
            )
            result = engine.extract_text(image_path)
            
            if result and result.get('text'):
                if self.enable_cache:
                    self._cache_result(image_path, result)
                return result
        
        # All engines failed
        logger.error(f"All OCR engines failed for {image_path}")
        return {
            'text': '',
            'confidence': 0.0,
            'engine': 'none',
            'metadata': {'error': 'All OCR engines failed'}
        }
    
    def _get_cache_key(self, image_path: str) -> str:
        """Generate cache key for image."""
        # Use file path and modification time for cache key
        path = Path(image_path)
        mtime = path.stat().st_mtime if path.exists() else 0
        key_str = f"{image_path}_{mtime}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cached_result(self, image_path: str) -> Optional[Dict]:
        """Get cached OCR result if available."""
        try:
            cache_key = self._get_cache_key(image_path)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if cache_file.exists():
                import json
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Cache read failed: {e}")
        
        return None
    
    def _cache_result(self, image_path: str, result: Dict) -> None:
        """Cache OCR result."""
        try:
            cache_key = self._get_cache_key(image_path)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            import json
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.debug(f"Cache write failed: {e}")


# Convenience function
def extract_text_from_image(
    image_path: str,
    engine: str = 'tesseract'
) -> Dict[str, Any]:
    """
    Quick convenience function to extract text from an image.
    
    Args:
        image_path: Path to image file
        engine: OCR engine to use ('tesseract' or 'paddleocr')
        
    Returns:
        OCR result dictionary
    """
    manager = OCRManager(preferred_engine=engine)
    return manager.extract_text(image_path)


# Made with Bob