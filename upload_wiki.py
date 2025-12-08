#!/usr/bin/env python3
"""
Upload CodeAgent Wiki to GitHub
This script clones the GitHub wiki repository and uploads all wiki pages.
"""

import os
import subprocess
import sys
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def print_step(message):
    print(f"{BLUE}📌 {message}{RESET}")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        print_error(f"Error: {e.stderr}")
        return None

def main():
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}  CodeAgent Wiki Upload to GitHub{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Step 1: Get current directory
    current_dir = Path.cwd()
    wiki_source_dir = current_dir / "wiki"
    wiki_repo_dir = current_dir / "DaveAgent.wiki"

    if not wiki_source_dir.exists():
        print_error(f"Wiki source directory not found: {wiki_source_dir}")
        sys.exit(1)

    print_step("Step 1: Checking wiki files...")
    wiki_files = list(wiki_source_dir.glob("*.md" ))
    if not wiki_files:
        print_error("No .md files found in wiki/ directory")
        sys.exit(1)
    
    print_success(f"Found {len(wiki_files)} wiki files")
    for f in sorted(wiki_files):
        print(f"  • {f.name}")
    print()

    # Step 2: Clone wiki repository
    print_step("Step 2: Cloning GitHub wiki repository...")
    
    if wiki_repo_dir.exists():
        print_warning("Wiki repository already exists. Removing it...")
        if os.name == 'nt':  # Windows
            run_command(f'rmdir /s /q "{wiki_repo_dir}"')
        else:  # Linux/macOS
            run_command(f'rm -rf "{wiki_repo_dir}"')
    
    wiki_url = "https://github.com/davidmonterocrespo24/DaveAgent.wiki.git"
    result = run_command(f'git clone "{wiki_url}"', cwd=current_dir)
    
    if result is None:
        print_error("Failed to clone wiki repository")
        print_warning("Make sure the wiki is enabled in GitHub Settings > Features > Wikis")
        sys.exit(1)
    
    print_success("Wiki repository cloned successfully\n")

    # Step 3: Copy wiki files
    print_step("Step 3: Copying wiki files...")
    
    copied_count = 0
    for source_file in wiki_files:
        dest_file = wiki_repo_dir / source_file.name
        try:
            content = source_file.read_text(encoding='utf-8')
            dest_file.write_text(content, encoding='utf-8')
            print(f"  • Copied: {source_file.name}")
            copied_count += 1
        except Exception as e:
            print_error(f"Failed to copy {source_file.name}: {e}")
    
    print_success(f"Copied {copied_count} files\n")

    # Step 4: Git add, commit, and push
    print_step("Step 4: Committing and pushing to GitHub...")
    
    # Configure git (in case it's not configured)
    run_command('git config user.name "DaveAgent Wiki Bot"', cwd=wiki_repo_dir)
    run_command('git config user.email "wiki@daveagent.ai"', cwd=wiki_repo_dir)
    
    # Add all files
    run_command('git add *.md', cwd=wiki_repo_dir)
    
    # Commit
    commit_msg = "Add comprehensive CodeAgent wiki documentation in English"
    result = run_command(f'git commit -m "{commit_msg}"', cwd=wiki_repo_dir)
    
    if result is None:
        print_warning("No changes to commit (wiki might already be up to date)")
    else:
        print_success("Changes committed")
    
    # Push
    print_step("Pushing to GitHub...")
    result = run_command('git push origin master', cwd=wiki_repo_dir)
    
    if result is None:
        print_error("Failed to push to GitHub")
        print_warning("You may need to authenticate with GitHub")
        sys.exit(1)
    
    print_success("Wiki pushed to GitHub successfully!\n")

    # Step 5: Summary
    print(f"{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}  ✨ Wiki Upload Complete!{RESET}")
    print(f"{GREEN}{'='* 60}{RESET}\n")
    
    wiki_web_url = "https://github.com/davidmonterocrespo24/DaveAgent/wiki"
    print(f"📚 Your wiki is now available at:")
    print(f"   {BLUE}{wiki_web_url}{RESET}\n")
    
    print("📝 Pages uploaded:")
    for f in sorted(wiki_files):
        page_name = f.stem  # filename without extension
        page_url = f"{wiki_web_url}/{page_name}"
        print(f"   • {page_name}: {page_url}")
    
    print(f"\n{GREEN}🎉 Congratulations! Your CodeAgent wiki is live!{RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Upload cancelled by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
