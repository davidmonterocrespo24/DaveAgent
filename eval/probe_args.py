import sys
from unittest.mock import MagicMock

# Mock resource
if sys.platform == 'win32':
    sys.modules['resource'] = MagicMock()

try:
    import inspect

    from swebench.harness.run_evaluation import main

    print(f"Signature: {inspect.signature(main)}")
    print(f"Docstring: {main.__doc__}")
except Exception as e:
    print(f"Error: {e}")
