"""
app.py
SENTINEL AI Application Entrypoint.
Delegates directly to main.py to start the multi-camera command center.

Usage:
    python app.py
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from main import main

if __name__ == "__main__":
    main()