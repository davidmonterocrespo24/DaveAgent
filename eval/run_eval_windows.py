import sys
import os
from unittest.mock import MagicMock

# MOCK RESOURCE MODULE FOR WINDOWS
# swebench imports 'resource' which is Unix-only. 
# We mock it before importing swebench to bypass the ModuleNotFoundError.
if sys.platform == 'win32':
    print("🪟 Windows detected: Mocking 'resource' module...")
    resource_mock = MagicMock()
    # these constants are often used, so we mock them just in case
    resource_mock.RLIMIT_AS = 9
    resource_mock.RLIMIT_CPU = 0
    sys.modules['resource'] = resource_mock

# Now we can import the harness
try:
    from swebench.harness.run_evaluation import main as run_evaluation
except ImportError as e:
    print(f"❌ Error importing swebench: {e}")
    sys.exit(1)

    # Call main with arguments directly
    print(f"🚀 Running SWE-bench evaluation...")

    # Defaults
    dataset_name = "princeton-nlp/SWE-bench_Verified"
    predictions_path = "predictions.jsonl"
    run_id = "evaluacion_prueba_v1"

    # Simple arg parsing for flexibility (optional override)
    for i, arg in enumerate(sys.argv):
        if arg == "--dataset_name" and i + 1 < len(sys.argv):
            dataset_name = sys.argv[i + 1]
        elif arg == "--predictions_path" and i + 1 < len(sys.argv):
            predictions_path = sys.argv[i + 1]
        elif arg == "--run_id" and i + 1 < len(sys.argv):
            run_id = sys.argv[i + 1]

    run_evaluation(
        dataset_name=dataset_name,
        predictions_path=predictions_path,
        run_id=run_id,
        max_workers=4,
        split='test'  # explicit split usually needed
    )
