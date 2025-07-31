#!/usr/bin/env python3
"""
Configuration validation script for StockAnalyzer
"""

import os
import sys

def test_config_loading():
    """Test configuration loading to catch any issues"""
    
    print("Testing Configuration Loading")
    print("=" * 35)
    
    try:
        # Test main config
        print("Testing main config.py...")
        sys.path.insert(0, os.path.dirname(__file__))
        import config
        
        print(f"✅ Main config loaded successfully")
        print(f"   GROQ_MODEL: {config.GROQ_MODEL}")
        print(f"   OLLAMA_MODEL: {config.OLLAMA_MODEL}")
        print(f"   OLLAMA_NUM_THREAD: {config.OLLAMA_NUM_THREAD}")
        print(f"   PDF_REPAIR_ENABLED: {config.PDF_REPAIR_ENABLED} (type: {type(config.PDF_REPAIR_ENABLED)})")
        print(f"   PDF_FALLBACK_TO_SINGLE_PAGE: {config.PDF_FALLBACK_TO_SINGLE_PAGE} (type: {type(config.PDF_FALLBACK_TO_SINGLE_PAGE)})")
        
    except Exception as e:
        print(f"❌ Main config failed: {e}")
        return False
    
    try:
        # Test server config
        print("\nTesting server/config.py...")
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))
        from server import config as server_config
        
        print(f"✅ Server config loaded successfully")
        print(f"   OLLAMA_MODEL: {server_config.OLLAMA_MODEL}")
        print(f"   PDF_REPAIR_ENABLED: {server_config.PDF_REPAIR_ENABLED} (type: {type(server_config.PDF_REPAIR_ENABLED)})")
        
    except Exception as e:
        print(f"❌ Server config failed: {e}")
        return False
    
    try:
        # Test tools config
        print("\nTesting tools/config.py...")
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
        from tools import config as tools_config
        
        print(f"✅ Tools config loaded successfully")
        print(f"   OLLAMA_MODEL: {tools_config.OLLAMA_MODEL}")
        print(f"   PDF_REPAIR_ENABLED: {tools_config.PDF_REPAIR_ENABLED} (type: {type(tools_config.PDF_REPAIR_ENABLED)})")
        
    except Exception as e:
        print(f"❌ Tools config failed: {e}")
        return False
    
    return True

def test_boolean_conversion():
    """Test the boolean conversion function"""
    
    print("\nTesting Boolean Conversion")
    print("=" * 30)
    
    sys.path.insert(0, os.path.dirname(__file__))
    from config import str_to_bool
    
    test_cases = [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("off", False),
        (True, True),
        (False, False),
        ("", False),
        ("random", False),
    ]
    
    all_passed = True
    for input_val, expected in test_cases:
        result = str_to_bool(input_val)
        if result == expected:
            print(f"✅ '{input_val}' -> {result}")
        else:
            print(f"❌ '{input_val}' -> {result} (expected {expected})")
            all_passed = False
    
    return all_passed

def main():
    """Main test function"""
    print("StockAnalyzer Configuration Validation")
    print("=" * 40)
    
    success = True
    
    # Test configuration loading
    if not test_config_loading():
        success = False
    
    # Test boolean conversion
    if not test_boolean_conversion():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All configuration tests passed!")
        print("The system should now start without configuration errors.")
    else:
        print("⚠️  Some configuration tests failed.")
        print("Please check the output above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
