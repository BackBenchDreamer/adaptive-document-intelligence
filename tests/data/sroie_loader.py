"""
SROIE2019 Dataset Loader

Loads and processes the SROIE2019 (Scanned Receipts OCR and Information Extraction) dataset.

Dataset structure expected:
tests/SROIE2019/
├── train/
│   ├── img/
│   │   ├── X00016469612.jpg
│   │   └── ...
│   └── box/
│       ├── X00016469612.txt
│       └── ...
└── test/
    ├── img/
    └── box/

Note: The dataset should be downloaded separately and placed in tests/SROIE2019/
This directory is excluded from git via .gitignore

Author: Adaptive Document Intelligence System
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def normalize_date(date_str: str) -> Optional[str]:
    """
    Normalize date string to ISO format (YYYY-MM-DD).
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        ISO formatted date string or None if invalid
    """
    if not date_str:
        return None
    
    # Try common date patterns
    patterns = [
        (r'(\d{2})/(\d{2})/(\d{4})', 'DD/MM/YYYY'),
        (r'(\d{4})-(\d{2})-(\d{2})', 'YYYY-MM-DD'),
        (r'(\d{2})-(\d{2})-(\d{4})', 'DD-MM-YYYY'),
    ]
    
    for pattern, format_type in patterns:
        match = re.match(pattern, date_str.strip())
        if match:
            if format_type == 'DD/MM/YYYY' or format_type == 'DD-MM-YYYY':
                day, month, year = match.groups()
                try:
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            elif format_type == 'YYYY-MM-DD':
                return date_str.strip()
    
    return None


def normalize_total(total_str: str) -> Optional[float]:
    """
    Normalize total amount string to float.
    
    Args:
        total_str: Amount string (e.g., "$12.34", "12.34", "12,34")
        
    Returns:
        Float amount or None if invalid
    """
    if not total_str:
        return None
    
    try:
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[$€£¥₹\s]', '', total_str)
        # Replace comma with dot for decimal
        cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


class SROIEDataLoader:
    """
    Loader for SROIE2019 dataset.
    
    Handles loading images and ground truth annotations for training and testing.
    """
    
    def __init__(
        self,
        dataset_root: str = 'tests/SROIE2019',
        split: str = 'train'
    ):
        """
        Initialize SROIE data loader.
        
        Args:
            dataset_root: Root directory of SROIE dataset
            split: 'train' or 'test'
        """
        self.dataset_root = Path(dataset_root)
        self.split = split
        
        self.img_dir = self.dataset_root / split / 'img'
        self.box_dir = self.dataset_root / split / 'box'
        
        # Check if dataset exists
        if not self.dataset_root.exists():
            logger.warning(
                f"SROIE dataset not found at {self.dataset_root}. "
                f"Please download it from: "
                f"https://rrc.cvc.uab.es/?ch=13&com=downloads"
            )
        
        logger.info(
            f"SROIEDataLoader initialized (split={split}, "
            f"root={self.dataset_root})"
        )
    
    def load_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load dataset samples.
        
        Args:
            limit: Maximum number of samples to load (None = all)
            
        Returns:
            List of sample dictionaries with structure:
            {
                'image_id': str,
                'image_path': str,
                'entities': {
                    'company': str,
                    'date': str,
                    'address': str,
                    'total': str
                }
            }
        """
        if not self.img_dir.exists():
            logger.error(f"Image directory not found: {self.img_dir}")
            return []
        
        # Get all image files
        image_files = sorted(self.img_dir.glob('*.jpg'))
        
        if limit:
            image_files = image_files[:limit]
        
        logger.info(f"Loading {len(image_files)} samples from {self.split} split")
        
        samples = []
        for img_path in image_files:
            sample = self._load_sample(img_path)
            if sample:
                samples.append(sample)
        
        logger.info(f"Loaded {len(samples)} valid samples")
        return samples
    
    def _load_sample(self, img_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load a single sample with image and annotations.
        
        Args:
            img_path: Path to image file
            
        Returns:
            Sample dictionary or None if loading failed
        """
        try:
            image_id = img_path.stem
            
            # Load ground truth if available
            entities = {}
            if self.box_dir.exists():
                box_file = self.box_dir / f"{image_id}.txt"
                if box_file.exists():
                    entities = self._parse_box_file(box_file)
            
            return {
                'image_id': image_id,
                'image_path': str(img_path),
                'entities': entities
            }
            
        except Exception as e:
            logger.error(f"Error loading sample {img_path}: {e}")
            return None
    
    def _parse_box_file(self, box_file: Path) -> Dict[str, str]:
        """
        Parse SROIE box file to extract entities.
        
        SROIE format:
        company,<company_name>
        date,<date>
        address,<address>
        total,<total_amount>
        
        Args:
            box_file: Path to box file
            
        Returns:
            Dictionary of entities
        """
        entities = {}
        
        try:
            with open(box_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or ',' not in line:
                        continue
                    
                    # Split on first comma only
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        value = parts[1].strip()
                        
                        # Map SROIE keys to our field names
                        if key == 'company':
                            entities['company'] = value
                        elif key == 'date':
                            entities['date'] = value
                        elif key == 'address':
                            entities['address'] = value
                        elif key == 'total':
                            entities['total'] = value
                        
                        # Also support alternative field names
                        elif key in ['invoice_number', 'receipt_number']:
                            entities['invoice_number'] = value
            
        except Exception as e:
            logger.error(f"Error parsing box file {box_file}: {e}")
        
        return entities
    
    def get_sample_by_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific sample by image ID.
        
        Args:
            image_id: Image ID (filename without extension)
            
        Returns:
            Sample dictionary or None if not found
        """
        img_path = self.img_dir / f"{image_id}.jpg"
        
        if not img_path.exists():
            logger.warning(f"Image not found: {img_path}")
            return None
        
        return self._load_sample(img_path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get dataset statistics.
        
        Returns:
            Dictionary with dataset statistics
        """
        samples = self.load_dataset()
        
        stats = {
            'total_samples': len(samples),
            'split': self.split,
            'fields_present': {
                'company': 0,
                'date': 0,
                'address': 0,
                'total': 0,
                'invoice_number': 0
            }
        }
        
        for sample in samples:
            entities = sample.get('entities', {})
            for field in stats['fields_present']:
                if field in entities and entities[field]:
                    stats['fields_present'][field] += 1
        
        return stats


# Convenience functions
def load_sroie_train(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load SROIE training set."""
    loader = SROIEDataLoader(split='train')
    return loader.load_dataset(limit=limit)


def load_sroie_test(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load SROIE test set."""
    loader = SROIEDataLoader(split='test')
    return loader.load_dataset(limit=limit)


# Made with Bob