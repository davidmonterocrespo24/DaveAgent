import argparse
import json
import os
import shutil
import asyncio
from datasets import load_dataset
from pathlib import Path
import subprocess

# Import our solver
from agent_wrapper import SWESolver


def clone_repo(repo, commit, work_dir):
    """
    Clones the repo and checks out the commit.
    repo: 'django/django'
    commit: sha
    work_dir: local path
    """
    repo_url = f"https://github.com/{repo}.git"

    # Use absolute path for work_dir
    work_dir = os.path.abspath(work_dir)

    if os.path.exists(work_dir):
        # Check if it is a git repo
        if os.path.exists(os.path.join(work_dir, ".git")):
            print(f"Repo {work_dir} exists. Cleaning and resetting...")
            subprocess.run(["git", "reset", "--hard"], cwd=work_dir, check=True)
            subprocess.run(["git", "clean", "-fd"], cwd=work_dir, check=True)
            subprocess.run(["git", "fetch", "repo_origin"], cwd=work_dir, check=False)  # Try fetching from alias
            if subprocess.run(["git", "fetch", "origin"], cwd=work_dir, check=False).returncode != 0:
                pass  # Warning or retry?
        else:
            # Weird state, delete and reclone
            print(f"Directory {work_dir} exists but not a git repo. Removing...")
            shutil.rmtree(work_dir)
            print(f"Cloning {repo} to {work_dir}...")
            subprocess.run(["git", "clone", repo_url, work_dir], check=True)
    else:
        print(f"Cloning {repo} to {work_dir}...")
        subprocess.run(["git", "clone", repo_url, work_dir], check=True)

    print(f"Checking out {commit}...")
    subprocess.run(["git", "checkout", "-f", commit], cwd=work_dir, check=True)


def get_diff(work_dir):
    result = subprocess.run(["git", "diff"], cwd=work_dir, capture_output=True, text=True)
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1, help="Number of tasks to run")
    parser.add_argument("--output", default="eval/predictions.jsonl", help="Output file")
    parser.add_argument("--repo_dir_base", default="eval/repos", help="Where to clone repos")
    parser.add_argument("--instance_id", help="Run a specific instance ID")
    args = parser.parse_args()

    print("Loading dataset...")
    try:
        dataset = load_dataset('princeton-nlp/SWE-bench_Verified', split='test')
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # Filter if needed
    if args.instance_id:
        dataset = dataset.filter(lambda x: x['instance_id'] == args.instance_id)
        if len(dataset) == 0:
            print(f"No instance found with ID {args.instance_id}")
            return
        print(f"Filtered to 1 instance: {args.instance_id}")
    else:
        # Take the first N
        dataset = dataset.select(range(min(len(dataset), args.limit)))
        print(f"Selected {len(dataset)} instances.")

    # Prepare output
    asyncio.run(run_tasks(dataset, args.repo_dir_base, args.output))


async def run_tasks(dataset, repo_dir_base, output_file):
    print("Initializing solver with deepseek-chat...")
    solver = SWESolver(model_override="deepseek-chat")

    # Create repos dir
    os.makedirs(repo_dir_base, exist_ok=True)

    try:
        for i, item in enumerate(dataset):
            instance_id = item['instance_id']
            repo = item['repo']
            base_commit = item['base_commit']
            problem_statement = item['problem_statement']

            print(f"\n[{i + 1}/{len(dataset)}] Processing {instance_id}...")

            repo_name = repo.split('/')[-1]
            work_dir = os.path.join(repo_dir_base, f"{repo_name}_{instance_id}")

            # Clone and setup
            try:
                clone_repo(repo, base_commit, work_dir)
            except Exception as e:
                print(f"Failed to clone/checkout: {e}")
                continue

            # Solve
            await solver.solve(problem_statement, work_dir)

            # Get patch
            patch = get_diff(work_dir)

            # If patch is empty, maybe the agent failed to edit?
            if not patch.strip():
                print("WARNING: No patch generated!")
            else:
                print(f"Patch generated ({len(patch)} chars).")

            results = {
                "instance_id": instance_id,
                "model_patch": patch,
                "model_name_or_path": "CodeAgent-v1"
            }

            # Append to file immediately
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(results) + "\n")

    finally:
        await solver.close()


if __name__ == "__main__":
    main()
