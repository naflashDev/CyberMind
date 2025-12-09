import os
import sys

# Ensure the project's `src/` directory is on sys.path so tests can import `app` package
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
