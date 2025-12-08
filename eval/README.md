# SWE-bench Evaluation for DaveAgent

This directory contains scripts to evaluate DaveAgent against the [SWE-bench Verified](https://www.swebench.com/) dataset.

## Setup

The scripts assume they are run from the project root `e:\AI\CodeAgent` (or equivalent) so that `src` is accessible.

## Scripts

### 1. `agent_wrapper.py`
A wrapper class `SWESolver` that interfaces with `DaveAgentCLI` (the agent's entry point).
It handles:
- Initializing the agent in "AGENTE" mode.
- Context switching (changing CWD to the target repository).
- Resetting agent memory between tasks.
- Running the agent on a problem statement.

### 2. `run_inference.py`
The main script to generate predictions.

Usage:
```bash
python swe_bench_eval/run_inference.py --limit <N> --instance_id <ID>
```

Arguments:
- `--limit`: Number of tasks to process (default: 1).
- `--repo_dir_base`: Directory to clone repositories (default: `repos`).
- `--output`: Output file for predictions (default: `predictions.jsonl`).
- `--instance_id`: Process a specific instance ID.

## Process
1. Loads the SWE-bench Verified dataset.
2. For each task:
   - Clones the repository to `swe_bench_eval/repos`.
   - Checks out the `base_commit`.
   - Runs `SWESolver` with the `problem_statement`.
   - Captures the changes using `git diff`.
   - Appends the result to `predictions.jsonl`.

## Next Steps (Evaluation)
Once `predictions.jsonl` is generated, use the SWE-bench harness to evaluate the patches:

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path swe_bench_eval/predictions.jsonl \
    --max_workers 4 \
    --run_id evaluation_v1
```
