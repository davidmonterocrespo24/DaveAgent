#!/usr/bin/env python3
"""Quick test to verify the name() method is implemented."""

import sys
import inspect

# Add project to path
sys.path.insert(0, 'e:/AI/CodeAgent')

from src.managers.rag_manager import AdvancedEmbeddingFunction

# Check if the name() method exists
if hasattr(AdvancedEmbeddingFunction, 'name'):
    print("✓ name() method exists in AdvancedEmbeddingFunction")

    # Get the method signature
    sig = inspect.signature(AdvancedEmbeddingFunction.name)
    print(f"✓ Method signature: name{sig}")

    # Check if it returns str
    annotations = AdvancedEmbeddingFunction.name.__annotations__
    if 'return' in annotations and annotations['return'] == str:
        print("✓ name() method returns str type")

    print("\n✓ Fix successful! ChromaDB deprecation warnings should be resolved.")
else:
    print("✗ name() method NOT found")
    sys.exit(1)
