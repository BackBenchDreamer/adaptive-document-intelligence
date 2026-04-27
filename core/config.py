"""
Configuration management for Adaptive Document Intelligence.

This module handles all configuration settings including:
- OCR engine settings
- Extraction parameters
- Confidence thresholds
- File paths and directories
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json


class Config:
    """Central configuration management class."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "ocr": {
            "engine": "easyocr",
            "languages": ["en"],
            "gpu": True,
            "confidence_threshold": 0.5,
        },
        "extraction": {
            "patterns": {
                "company": r"(?i)company|corporation|inc|ltd",
                "date": r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",
                "total": r"(?i)total|amount|sum",
                "address": r"\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd)",
            },
            "field_confidence_threshold": 0.6,
        },
        "confidence": {
            "weights": {
                "ocr_confidence": 0.3,
                "pattern_match": 0.3,
                "context_score": 0.2,
                "position_score": 0.2,
            },
            "min_confidence": 0.5,
        },
        "paths": {
            "data_dir": "data",
            "output_dir": "output",
            "cache_dir": "output/cache",
            "models_dir": "models",
        },
    }
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration.
        
        Args:
            config_dict: Optional dictionary to override default config
        """
        self.config = self.DEFAULT_CONFIG.copy()
        if config_dict:
            self._update_config(config_dict)
        
        # Load from environment variables
        self._load_from_env()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _update_config(self, config_dict: Dict[str, Any]) -> None:
        """Recursively update configuration."""
        def update_recursive(base: Dict, updates: Dict) -> None:
            for key, value in updates.items():
                if isinstance(value, dict) and key in base:
                    update_recursive(base[key], value)
                else:
                    base[key] = value
        
        update_recursive(self.config, config_dict)
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # OCR settings
        if os.getenv("OCR_ENGINE"):
            self.config["ocr"]["engine"] = os.getenv("OCR_ENGINE")
        if os.getenv("OCR_GPU"):
            self.config["ocr"]["gpu"] = os.getenv("OCR_GPU").lower() == "true"
        
        # Paths
        if os.getenv("DATA_DIR"):
            self.config["paths"]["data_dir"] = os.getenv("DATA_DIR")
        if os.getenv("OUTPUT_DIR"):
            self.config["paths"]["output_dir"] = os.getenv("OUTPUT_DIR")
    
    def _ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        for path_key, path_value in self.config["paths"].items():
            Path(path_value).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., "ocr.engine")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., "ocr.engine")
            value: Value to set
        """
        keys = key.split(".")
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self.config.copy()
    
    def save(self, filepath: str) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            filepath: Path to save configuration
        """
        with open(filepath, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'Config':
        """
        Load configuration from JSON file.
        
        Args:
            filepath: Path to configuration file
            
        Returns:
            Config instance
        """
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls(config_dict)
    
    def __repr__(self) -> str:
        return f"Config({json.dumps(self.config, indent=2)})"


# Global configuration instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def set_config(config: Config) -> None:
    """Set global configuration instance."""
    global _global_config
    _global_config = config

# Made with Bob
