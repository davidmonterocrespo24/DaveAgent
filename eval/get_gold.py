from datasets import load_dataset
import sys

instance_id = "astropy__astropy-12907"
print(f"Loading dataset for {instance_id}...")
dataset = load_dataset('princeton-nlp/SWE-bench_Verified', split='test')
# Filter
filtered = dataset.filter(lambda x: x['instance_id'] == instance_id)

if len(filtered) > 0:
    entry = filtered[0]
    print(f"--- Gold Patch for {instance_id} ---")
    print(entry['patch'])
else:
    print("Instance not found.")
