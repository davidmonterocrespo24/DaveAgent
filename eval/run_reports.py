#!/usr/bin/env python3
"""
Wrapper script para ejecutar generate_detailed_report.py con encoding UTF-8
Resuelve problemas de encoding en Windows
"""

import sys

# Force UTF-8 encoding for stdout/stderr in Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Import and run the main script
from generate_detailed_report import main

if __name__ == "__main__":
    main()
