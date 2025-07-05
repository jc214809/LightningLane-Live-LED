import sys
import os

# Ensure test stubs override real modules if missing
stubs_dir = os.path.join(os.path.dirname(__file__), 'stubs')
if stubs_dir not in sys.path:
    sys.path.insert(0, stubs_dir)
