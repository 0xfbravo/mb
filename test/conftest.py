"""
Pytest configuration file.

This file sets up the Python path to include the project root directory,
allowing tests to import modules from the main application.
"""

import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
