"""
Simple test script for the Invoice OCR API
Usage: python test_api.py <path_to_invoice_image>
"""

import requests
import sys
import json

API_URL = "http://localhost:8000/upload"

def test_upload(file_path: str):
    """Test the upload endpoint with an invoice image"""
    
    print(f"Testing API with file: {file_path}")
    print("-" * 50)
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'image/jpeg')}
            response = requests.post(API_URL, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Success!")
            print("\nExtracted Data:")
            print(json.dumps(result['extracted_data'], indent=2))
            print("\nRaw Text Preview:")
            print(result.get('raw_text', '')[:200])
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.json())
    
    except FileNotFoundError:
        print(f"✗ Error: File not found: {file_path}")
    except requests.exceptions.ConnectionError:
        print("✗ Error: Cannot connect to API. Is the server running?")
        print("Start the server with: cd backend && python main.py")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <path_to_invoice_image>")
        sys.exit(1)
    
    test_upload(sys.argv[1])

# Made with Bob
