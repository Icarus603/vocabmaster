#!/usr/bin/env python3
import sys
import os

print("Testing PyQt6 import...")
try:
    from PyQt6.QtWidgets import QApplication
    print("✅ PyQt6.QtWidgets imported successfully")
    
    from PyQt6.QtCore import QCoreApplication
    print("✅ PyQt6.QtCore imported successfully")
    
    # Test creating QCoreApplication
    app = QCoreApplication(sys.argv)
    print("✅ QCoreApplication created successfully")
    
    print("✅ Qt test passed!")
    sys.exit(0)
except Exception as e:
    print(f"❌ Qt test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)