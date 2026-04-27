"""
Setup verification script
Run this to verify all dependencies are installed correctly
"""

import sys

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ⚠ Warning: Python 3.8+ recommended")
        return False
    return True

def check_tesseract():
    """Check if Tesseract is installed"""
    try:
        import subprocess
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        version_line = result.stdout.split('\n')[0]
        print(f"✓ {version_line}")
        return True
    except FileNotFoundError:
        print("✗ Tesseract OCR not found")
        print("  Install with: brew install tesseract (macOS)")
        print("  or: sudo apt-get install tesseract-ocr (Ubuntu)")
        return False

def check_python_packages():
    """Check if required Python packages are installed"""
    packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pytesseract': 'pytesseract',
        'PIL': 'Pillow'
    }
    
    all_installed = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} not installed")
            all_installed = False
    
    return all_installed

def main():
    print("=" * 50)
    print("Invoice OCR API - Setup Verification")
    print("=" * 50)
    print()
    
    checks = [
        ("Python Version", check_python_version()),
        ("Tesseract OCR", check_tesseract()),
        ("Python Packages", check_python_packages())
    ]
    
    print()
    print("=" * 50)
    
    if all(result for _, result in checks):
        print("✓ All checks passed! You're ready to run the API.")
        print()
        print("Start the server with:")
        print("  python main.py")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print()
        print("See docs/SETUP.md for detailed installation instructions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
