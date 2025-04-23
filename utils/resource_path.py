"""Resource path utility module.

This module provides utility functions for accessing resources in both
development and PyInstaller-packaged environments.
"""

import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    try:
        # If running in a PyInstaller bundle
        base_path = sys._MEIPASS
    except Exception:
        # If running in normal Python environment
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    return os.path.join(base_path, relative_path)
