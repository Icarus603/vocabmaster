#!/usr/bin/env python3
import sys
import os

# Set environment for minimal Qt setup
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

print("Testing minimal PyQt6 import...")
try:
    from PyQt6.QtCore import QCoreApplication
    print("✅ PyQt6.QtCore imported successfully")
    
    # Test creating QCoreApplication without GUI
    app = QCoreApplication([])
    print("✅ QCoreApplication created successfully")
    
    print("✅ Minimal Qt test passed!")
    sys.exit(0)
except Exception as e:
    print(f"❌ Minimal Qt test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)