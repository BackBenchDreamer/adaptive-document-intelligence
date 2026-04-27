#!/usr/bin/env python3
"""
System Validation Script for Adaptive Document Intelligence System

This script performs comprehensive validation of the system including:
- Import integrity checks
- Core functionality verification
- Module instantiation tests
- Basic sanity checks

Usage:
    python validate_system.py
"""

import sys
import traceback
from typing import Dict, List, Tuple


class SystemValidator:
    """Validates the Adaptive Document Intelligence System."""
    
    def __init__(self):
        self.results = {
            'imports': {},
            'functionality': {},
            'overall': True
        }
    
    def validate_imports(self) -> Dict[str, bool]:
        """Test that all core modules can be imported."""
        print("=" * 70)
        print("VALIDATING IMPORTS")
        print("=" * 70)
        
        import_tests = {
            # Core modules
            'core.config': 'from core.config import Config',
            'core.logging_config': 'from core.logging_config import get_logger',
            'core.utils': 'from core.utils import ensure_dir, load_json, save_json',
            
            # Pipeline modules
            'pipeline.ocr': 'from pipeline.ocr import OCRManager, TesseractEngine',
            'pipeline.extractor': 'from pipeline.extractor import FieldExtractor',
            'pipeline.confidence': 'from pipeline.confidence import ConfidenceManager',
            'pipeline.pipeline': 'from pipeline.pipeline import DocumentProcessor',
            
            # Test data loader
            'tests.data.sroie_loader': 'from tests.data.sroie_loader import SROIEDataLoader',
            
            # Test evaluation
            'tests.metrics.evaluation': 'from tests.metrics.evaluation import DocumentEvaluator',
            'tests.analysis.error_analysis': 'from tests.analysis.error_analysis import ErrorAnalyzer',
        }
        
        results = {}
        for module_name, import_statement in import_tests.items():
            try:
                exec(import_statement)
                results[module_name] = True
                print(f"✅ {module_name:40s} SUCCESS")
            except Exception as e:
                results[module_name] = False
                self.results['overall'] = False
                print(f"❌ {module_name:40s} FAILED: {str(e)}")
        
        self.results['imports'] = results
        return results
    
    def validate_core_functionality(self) -> Dict[str, bool]:
        """Verify core functionality with minimal tests."""
        print("\n" + "=" * 70)
        print("VALIDATING CORE FUNCTIONALITY")
        print("=" * 70)
        
        tests = {}
        
        # Test 1: DocumentProcessor instantiation
        try:
            from pipeline.pipeline import DocumentProcessor
            processor = DocumentProcessor(ocr_engine='tesseract')
            
            # Verify methods exist
            assert hasattr(processor, 'process_document'), "Missing process_document method"
            assert hasattr(processor, 'process_batch'), "Missing process_batch method"
            
            tests['DocumentProcessor instantiation'] = True
            print("✅ DocumentProcessor instantiation        SUCCESS")
        except Exception as e:
            tests['DocumentProcessor instantiation'] = False
            self.results['overall'] = False
            print(f"❌ DocumentProcessor instantiation        FAILED: {str(e)}")
        
        # Test 2: OCRManager instantiation
        try:
            from pipeline.ocr import OCRManager
            ocr_manager = OCRManager(preferred_engine='tesseract')
            
            assert hasattr(ocr_manager, 'extract_text'), "Missing extract_text method"
            
            tests['OCRManager instantiation'] = True
            print("✅ OCRManager instantiation               SUCCESS")
        except Exception as e:
            tests['OCRManager instantiation'] = False
            self.results['overall'] = False
            print(f"❌ OCRManager instantiation               FAILED: {str(e)}")
        
        # Test 3: ExtractionManager instantiation
        try:
            from pipeline.extractor import ExtractionManager
            extractor = ExtractionManager()
            
            assert hasattr(extractor, 'extract_fields'), "Missing extract_fields method"
            
            tests['ExtractionManager instantiation'] = True
            print("✅ ExtractionManager instantiation        SUCCESS")
        except Exception as e:
            tests['ExtractionManager instantiation'] = False
            self.results['overall'] = False
            print(f"❌ ExtractionManager instantiation        FAILED: {str(e)}")
        
        # Test 4: ConfidenceManager instantiation
        try:
            from pipeline.confidence import ConfidenceManager
            confidence_mgr = ConfidenceManager()
            
            assert hasattr(confidence_mgr, 'score_extraction'), "Missing score_extraction method"
            
            tests['ConfidenceManager instantiation'] = True
            print("✅ ConfidenceManager instantiation        SUCCESS")
        except Exception as e:
            tests['ConfidenceManager instantiation'] = False
            self.results['overall'] = False
            print(f"❌ ConfidenceManager instantiation        FAILED: {str(e)}")
        
        # Test 5: Config loading
        try:
            from core.config import Config
            config = Config()
            
            assert hasattr(config, 'config'), "Missing config attribute"
            assert 'ocr' in config.config, "Missing ocr config"
            assert 'extraction' in config.config, "Missing extraction config"
            
            tests['Config loading'] = True
            print("✅ Config loading                         SUCCESS")
        except Exception as e:
            tests['Config loading'] = False
            self.results['overall'] = False
            print(f"❌ Config loading                         FAILED: {str(e)}")
        
        # Test 6: Logger initialization
        try:
            from core.logging_config import get_logger
            logger = get_logger(__name__)
            
            assert hasattr(logger, 'info'), "Missing info method"
            assert hasattr(logger, 'error'), "Missing error method"
            
            tests['Logger initialization'] = True
            print("✅ Logger initialization                  SUCCESS")
        except Exception as e:
            tests['Logger initialization'] = False
            self.results['overall'] = False
            print(f"❌ Logger initialization                  FAILED: {str(e)}")
        
        # Test 7: Utility functions
        try:
            from core.utils import ensure_dir, load_json, save_json
            
            assert callable(ensure_dir), "ensure_dir not callable"
            assert callable(load_json), "load_json not callable"
            assert callable(save_json), "save_json not callable"
            
            tests['Utility functions'] = True
            print("✅ Utility functions                      SUCCESS")
        except Exception as e:
            tests['Utility functions'] = False
            self.results['overall'] = False
            print(f"❌ Utility functions                      FAILED: {str(e)}")
        
        self.results['functionality'] = tests
        return tests
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        
        # Import results
        import_success = sum(1 for v in self.results['imports'].values() if v)
        import_total = len(self.results['imports'])
        print(f"\nImport Tests:        {import_success}/{import_total} passed")
        
        # Functionality results
        func_success = sum(1 for v in self.results['functionality'].values() if v)
        func_total = len(self.results['functionality'])
        print(f"Functionality Tests: {func_success}/{func_total} passed")
        
        # Overall status
        print(f"\nOverall Status:      {'✅ PASS' if self.results['overall'] else '❌ FAIL'}")
        
        if not self.results['overall']:
            print("\n⚠️  Some tests failed. Please review the output above for details.")
            return 1
        else:
            print("\n✅ All validation tests passed successfully!")
            print("   The system is ready for deployment.")
            return 0


def main():
    """Main validation entry point."""
    print("\n" + "=" * 70)
    print("ADAPTIVE DOCUMENT INTELLIGENCE SYSTEM - VALIDATION")
    print("=" * 70)
    print()
    
    validator = SystemValidator()
    
    try:
        # Run validation tests
        validator.validate_imports()
        validator.validate_core_functionality()
        
        # Print summary and return exit code
        exit_code = validator.print_summary()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during validation: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

# Made with Bob
