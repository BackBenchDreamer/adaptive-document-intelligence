#!/usr/bin/env python3
"""
OCR Environment Diagnostic Script
Comprehensive check of Tesseract OCR and pytesseract installation
"""

import sys
import os
import subprocess
from pathlib import Path

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_pytesseract_package():
    """Check if pytesseract Python package is installed"""
    print_section("1. PYTESSERACT PYTHON PACKAGE CHECK")
    
    try:
        import pytesseract
        print("✓ pytesseract is INSTALLED")
        
        # Try to get version
        try:
            version = pytesseract.__version__
            print(f"  Version: {version}")
        except AttributeError:
            print("  Version: Unable to determine (no __version__ attribute)")
        
        # Get module location
        try:
            location = pytesseract.__file__
            print(f"  Location: {location}")
        except AttributeError:
            print("  Location: Unable to determine")
        
        return True, pytesseract
        
    except ImportError as e:
        print("✗ pytesseract is NOT INSTALLED")
        print(f"  Import Error: {e}")
        return False, None
    except Exception as e:
        print(f"✗ Unexpected error importing pytesseract: {e}")
        return False, None

def check_tesseract_binary():
    """Check if Tesseract binary is available"""
    print_section("2. TESSERACT BINARY CHECK")
    
    # Check with 'which' command
    print("\n[A] Using 'which tesseract':")
    try:
        result = subprocess.run(['which', 'tesseract'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            path = result.stdout.strip()
            print(f"✓ Found at: {path}")
        else:
            print("✗ Not found in PATH")
    except Exception as e:
        print(f"✗ Error running 'which': {e}")
    
    # Check version
    print("\n[B] Using 'tesseract --version':")
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✓ Tesseract is executable")
            print("  Output:")
            for line in result.stdout.split('\n')[:5]:  # First 5 lines
                if line.strip():
                    print(f"    {line}")
        else:
            print("✗ Tesseract command failed")
            print(f"  stderr: {result.stderr}")
    except FileNotFoundError:
        print("✗ Tesseract command not found")
    except Exception as e:
        print(f"✗ Error running tesseract: {e}")
    
    # Check common installation paths
    print("\n[C] Checking common installation paths:")
    common_paths = [
        '/opt/homebrew/bin/tesseract',  # macOS Homebrew (Apple Silicon)
        '/usr/local/bin/tesseract',      # macOS Homebrew (Intel) / Linux
        '/usr/bin/tesseract',            # Linux system
        '/opt/local/bin/tesseract',      # MacPorts
    ]
    
    found_paths = []
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            print(f"✓ Found: {path}")
            found_paths.append(path)
        else:
            print(f"✗ Not found: {path}")
    
    return found_paths

def test_pytesseract_integration(pytesseract_module, tesseract_paths):
    """Test pytesseract integration with Tesseract binary"""
    print_section("3. PYTESSERACT INTEGRATION TEST")
    
    if pytesseract_module is None:
        print("⊘ Skipped: pytesseract not installed")
        return
    
    # Test 1: Default configuration
    print("\n[A] Testing with default configuration:")
    try:
        version = pytesseract_module.get_tesseract_version()
        print(f"✓ Successfully connected to Tesseract")
        print(f"  Version: {version}")
    except Exception as e:
        print(f"✗ Failed to connect to Tesseract")
        print(f"  Error: {type(e).__name__}: {e}")
    
    # Test 2: Check configured path
    print("\n[B] Checking pytesseract.tesseract_cmd configuration:")
    try:
        cmd = pytesseract_module.pytesseract.tesseract_cmd
        print(f"  Current setting: {cmd}")
        
        if cmd and os.path.isfile(cmd):
            print(f"✓ Configured path exists: {cmd}")
        elif cmd:
            print(f"✗ Configured path does NOT exist: {cmd}")
        else:
            print("  Using default (searching in PATH)")
    except Exception as e:
        print(f"  Error checking configuration: {e}")
    
    # Test 3: Try explicit paths
    if tesseract_paths:
        print("\n[C] Testing with explicit paths:")
        for path in tesseract_paths:
            print(f"\n  Testing: {path}")
            try:
                original_cmd = pytesseract_module.pytesseract.tesseract_cmd
                pytesseract_module.pytesseract.tesseract_cmd = path
                version = pytesseract_module.get_tesseract_version()
                print(f"  ✓ Success with version: {version}")
                pytesseract_module.pytesseract.tesseract_cmd = original_cmd
            except Exception as e:
                print(f"  ✗ Failed: {type(e).__name__}: {e}")
                pytesseract_module.pytesseract.tesseract_cmd = original_cmd

def check_requirements_file():
    """Check if pytesseract is in requirements.txt"""
    print_section("4. REQUIREMENTS.TXT CHECK")
    
    req_file = Path('requirements.txt')
    
    if not req_file.exists():
        print("✗ requirements.txt not found in current directory")
        return
    
    print(f"✓ Found: {req_file.absolute()}")
    
    try:
        content = req_file.read_text()
        lines = content.split('\n')
        
        pytesseract_found = False
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                if 'pytesseract' in line.lower():
                    print(f"✓ pytesseract found at line {i}: {line}")
                    pytesseract_found = True
        
        if not pytesseract_found:
            print("✗ pytesseract NOT found in requirements.txt")
            print("\n  Searching for OCR-related packages:")
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['ocr', 'tesseract', 'pillow', 'opencv']):
                    print(f"    Line {i}: {line}")
    
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")

def check_python_environment():
    """Check Python environment details"""
    print_section("5. PYTHON ENVIRONMENT")
    
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Path: {sys.path[0]}")
    
    # Check if in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Running in virtual environment")
        print(f"  Virtual env: {sys.prefix}")
    else:
        print("⚠ Not running in virtual environment")

def main():
    """Run all diagnostic checks"""
    print("\n" + "=" * 70)
    print("  TESSERACT OCR ENVIRONMENT DIAGNOSTIC")
    print("  Adaptive Document Intelligence System")
    print("=" * 70)
    print(f"\nCurrent Directory: {os.getcwd()}")
    
    # Run all checks
    check_python_environment()
    pytesseract_installed, pytesseract_module = check_pytesseract_package()
    tesseract_paths = check_tesseract_binary()
    test_pytesseract_integration(pytesseract_module, tesseract_paths)
    check_requirements_file()
    
    # Summary
    print_section("DIAGNOSTIC SUMMARY")
    print(f"pytesseract package: {'INSTALLED' if pytesseract_installed else 'NOT INSTALLED'}")
    print(f"Tesseract binary: {'FOUND' if tesseract_paths else 'NOT FOUND'}")
    
    if pytesseract_installed and tesseract_paths:
        print("\n✓ Both components present - configuration issue likely")
    elif not pytesseract_installed and tesseract_paths:
        print("\n⚠ Tesseract binary found but pytesseract package missing")
    elif pytesseract_installed and not tesseract_paths:
        print("\n⚠ pytesseract package found but Tesseract binary missing")
    else:
        print("\n✗ Both components missing")
    
    print("\n" + "=" * 70)
    print("  END OF DIAGNOSTIC")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

# Made with Bob
