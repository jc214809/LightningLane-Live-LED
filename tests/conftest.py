import os
import sys

# Add the stubs directory to sys.path so tests use stub modules
STUBS_DIR = os.path.join(os.path.dirname(__file__), 'stubs')
if STUBS_DIR not in sys.path:
    sys.path.insert(0, STUBS_DIR)
