"""
Integration test configuration file.

This file ensures that integration tests can import modules from the main application.
"""

import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
