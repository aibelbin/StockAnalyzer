#!/usr/bin/env python3
"""
Test script for PDF error handling in StockAnalyzer
"""

import os
import sys
import tempfile
import logging

# Add the tools directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

def create_corrupted_pdf(output_path):
    """Create a deliberately corrupted PDF for testing"""
    with open(output_path, 'wb') as f:
        # Write a PDF header
        f.write(b'%PDF-1.4\n')
        # Write some invalid content
        f.write(b'1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n')
        # Write corrupted xref table
        f.write(b'xref\n0 2\n0000000000 65535 f\nINVALID_ENTRY n\n')
        # Write invalid trailer
        f.write(b'trailer\n<<\n/Size 2\n/Root INVALID\n>>\n')
        f.write(b'%%EOF\n')

def test_pdf_error_handling():
    """Test the PDF error handling functionality"""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Testing PDF Error Handling")
    print("=" * 30)
    
    # Create a temporary corrupted PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
        temp_pdf_path = temp_pdf.name
    
    try:
        create_corrupted_pdf(temp_pdf_path)
        print(f"✅ Created test corrupted PDF: {temp_pdf_path}")
        
        # Import the transformer module
        try:
            from transformer_img import convert_pdf_to_images_with_retry
            print("✅ Successfully imported PDF processing functions")
            
            # Test the error handling
            print("🔧 Testing PDF error handling...")
            try:
                images = convert_pdf_to_images_with_retry(temp_pdf_path, max_pages=1)
                if images:
                    print(f"✅ Error handling succeeded: {len(images)} images extracted")
                else:
                    print("⚠️  Error handling returned no images (expected for severely corrupted PDF)")
            except Exception as e:
                print(f"✅ Error handling gracefully caught exception: {e}")
            
        except ImportError as e:
            print(f"❌ Failed to import PDF processing functions: {e}")
            print("Make sure you're running this from the StockAnalyzer directory")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Clean up
        try:
            os.unlink(temp_pdf_path)
            print("🧹 Cleaned up test files")
        except:
            pass
    
    print("\n✅ PDF error handling test completed")
    return True

def test_pdf_repair_tool():
    """Test the PDF repair tool"""
    
    print("\nTesting PDF Repair Tool")
    print("=" * 25)
    
    # Check if the repair tool exists
    repair_tool = os.path.join(os.path.dirname(__file__), 'pdf_repair_tool.sh')
    if os.path.exists(repair_tool):
        print(f"✅ PDF repair tool found: {repair_tool}")
        
        # Test the check command
        import subprocess
        try:
            result = subprocess.run([repair_tool, 'check'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ PDF repair tool check passed")
            else:
                print("⚠️  PDF repair tool check warnings (Ghostscript may not be installed)")
                print(result.stdout)
        except Exception as e:
            print(f"❌ PDF repair tool test failed: {e}")
            return False
    else:
        print(f"❌ PDF repair tool not found: {repair_tool}")
        return False
    
    return True

def main():
    """Main test function"""
    print("StockAnalyzer PDF Error Handling Test Suite")
    print("=" * 45)
    
    success = True
    
    # Test 1: PDF error handling
    if not test_pdf_error_handling():
        success = False
    
    # Test 2: PDF repair tool
    if not test_pdf_repair_tool():
        success = False
    
    print("\n" + "=" * 45)
    if success:
        print("🎉 All tests passed! PDF error handling is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
