"""
Git operations support for MCP File Editor.
Provides git functionality for both local and remote (SSH) repositories.
"""

import asyncio
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

from file_operations import FileOperationsInterface, LocalFileOperations, SSHFileOperations


class GitOperationsInterface:
    """Interface for git operations that can work on both local and remote systems."""
    
    async def run_git_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[str, str, int]:
        """Run a git command and return stdout, stderr, and return code."""
        raise NotImplementedError
    
    async def is_git_repository(self, path: Path) -> bool:
        """Check if a path is inside a git repository."""
        raise NotImplementedError


class LocalGitOperations(GitOperationsInterface):
    """Local git operations using subprocess."""
    
    def __init__(self):
        self.file_ops = LocalFileOperations()
    
    async def run_git_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[str, str, int]:
        """Run a git command locally."""
        import subprocess
        
        # Prepend 'git' to the command
        full_command = ['git'] + command
        
        # Run the command
        proc = await asyncio.create_subprocess_exec(
            *full_command,
            cwd=str(cwd) if cwd else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        return (
            stdout.decode('utf-8', errors='replace'),
            stderr.decode('utf-8', errors='replace'),
            proc.returncode or 0
        )
    
    async def is_git_repository(self, path: Path) -> bool:
        """Check if a path is inside a git repository."""
        stdout, _, returncode = await self.run_git_command(['rev-parse', '--git-dir'], cwd=path)
        return returncode == 0


class SSHGitOperations(GitOperationsInterface):
    """Remote git operations over SSH."""
    
    def __init__(self, conn, sftp):
        self.conn = conn
        self.sftp = sftp
        self.file_ops = SSHFileOperations(conn, sftp)
    
    async def run_git_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[str, str, int]:
        """Run a git command on remote server via SSH."""
        # Build the full command
        full_command = 'git ' + ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in command)
        
        # Add cd to working directory if specified
        if cwd:
            full_command = f'cd "{cwd}" && {full_command}'
        
        # Run the command
        result = await self.conn.run(full_command, check=False)
        
        return (
            result.stdout,
            result.stderr,
            result.returncode
        )
    
    async def is_git_repository(self, path: Path) -> bool:
        """Check if a path is inside a git repository."""
        stdout, _, returncode = await self.run_git_command(['rev-parse', '--git-dir'], cwd=path)
        return returncode == 0


class GitOperations:
    """High-level git operations that work with both local and remote repositories."""
    
    def __init__(self, git_ops: GitOperationsInterface, file_ops: FileOperationsInterface, project_dir: Path):
        self.git_ops = git_ops
        self.file_ops = file_ops
        self.project_dir = project_dir
    
    async def status(self, path: Optional[Path] = None) -> Dict[str, Any]:
        """Get git repository status."""
        work_dir = path or self.project_dir
        
        # Check if it's a git repository
        if not await self.git_ops.is_git_repository(work_dir):
            return {
                "is_repository": False,
                "error": "Not a git repository"
            }
        
        # Get status
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            ['status', '--porcelain=v1', '-b'],
            cwd=work_dir
        )
        
        if returncode != 0:
            return {
                "is_repository": True,
                "error": stderr,
                "returncode": returncode
            }
        
        # Parse status output
        lines = stdout.strip().split('\n') if stdout.strip() else []
        
        # First line contains branch info
        branch_line = lines[0] if lines else ""
        branch_match = re.match(r'## (.+?)(?:\.{3}(.+?))?(?:\s+\[(.+?)\])?$', branch_line)
        
        current_branch = ""
        tracking_branch = ""
        ahead_behind = ""
        
        if branch_match:
            current_branch = branch_match.group(1)
            tracking_branch = branch_match.group(2) or ""
            ahead_behind = branch_match.group(3) or ""
        
        # Parse file statuses
        staged = []
        modified = []
        untracked = []
        deleted = []
        
        for line in lines[1:]:
            if not line:
                continue
            
            status = line[:2]
            filename = line[3:]
            
            if status == '??':
                untracked.append(filename)
            elif status[0] in 'MADRC':
                staged.append({"status": status[0], "file": filename})
            elif status[1] in 'MD':
                if status[1] == 'M':
                    modified.append(filename)
                else:
                    deleted.append(filename)
        
        return {
            "is_repository": True,
            "branch": current_branch,
            "tracking_branch": tracking_branch,
            "ahead_behind": ahead_behind,
            "staged": staged,
            "modified": modified,
            "untracked": untracked,
            "deleted": deleted,
            "clean": len(staged) == 0 and len(modified) == 0 and len(untracked) == 0 and len(deleted) == 0
        }
    
    async def init(self, path: Optional[Path] = None) -> Dict[str, Any]:
        """Initialize a new git repository."""
        work_dir = path or self.project_dir
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            ['init'],
            cwd=work_dir
        )
        
        return {
            "success": returncode == 0,
            "path": str(work_dir),
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    
    async def clone(self, url: str, path: Optional[Path] = None, branch: Optional[str] = None) -> Dict[str, Any]:
        """Clone a remote repository."""
        work_dir = path or self.project_dir
        
        command = ['clone', url, str(work_dir)]
        if branch:
            command.extend(['-b', branch])
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(command)
        
        return {
            "success": returncode == 0,
            "url": url,
            "path": str(work_dir),
            "branch": branch,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    
    async def add(self, files: Union[str, List[str]], path: Optional[Path] = None) -> Dict[str, Any]:
        """Add files to git staging area."""
        work_dir = path or self.project_dir
        
        if isinstance(files, str):
            files = [files]
        
        command = ['add'] + files
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            command,
            cwd=work_dir
        )
        
        return {
            "success": returncode == 0,
            "files": files,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    
    async def commit(self, message: str, path: Optional[Path] = None) -> Dict[str, Any]:
        """Commit staged changes."""
        work_dir = path or self.project_dir
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            ['commit', '-m', message],
            cwd=work_dir
        )
        
        # Extract commit hash if successful
        commit_hash = ""
        if returncode == 0:
            match = re.search(r'\[.*\s+([a-f0-9]+)\]', stdout)
            if match:
                commit_hash = match.group(1)
        
        return {
            "success": returncode == 0,
            "message": message,
            "commit_hash": commit_hash,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    
    async def push(self, remote: str = "origin", branch: Optional[str] = None, 
                   path: Optional[Path] = None, set_upstream: bool = False) -> Dict[str, Any]:
        """Push commits to remote repository."""
        work_dir = path or self.project_dir
        
        command = ['push', remote]
        if branch:
            command.append(branch)
        if set_upstream:
            command.insert(1, '-u')
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            command,
            cwd=work_dir
        )
        
        return {
            "success": returncode == 0,
            "remote": remote,
            "branch": branch,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    
    async def pull(self, remote: str = "origin", branch: Optional[str] = None,
                   path: Optional[Path] = None) -> Dict[str, Any]:
        """Pull changes from remote repository."""
        work_dir = path or self.project_dir
        
        command = ['pull', remote]
        if branch:
            command.append(branch)
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            command,
            cwd=work_dir
        )
        
        return {
            "success": returncode == 0,
            "remote": remote,
            "branch": branch,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    
    async def log(self, limit: int = 10, oneline: bool = True, 
                  path: Optional[Path] = None) -> Dict[str, Any]:
        """Get git commit log."""
        work_dir = path or self.project_dir
        
        command = ['log', f'-{limit}']
        if oneline:
            command.append('--oneline')
        else:
            command.extend(['--pretty=format:%H|%an|%ae|%ad|%s', '--date=iso'])
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            command,
            cwd=work_dir
        )
        
        commits = []
        if returncode == 0 and stdout:
            if oneline:
                commits = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
            else:
                for line in stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|', 4)
                        if len(parts) == 5:
                            commits.append({
                                "hash": parts[0],
                                "author": parts[1],
                                "email": parts[2],
                                "date": parts[3],
                                "message": parts[4]
                            })
        
        return {
            "success": returncode == 0,
            "commits": commits,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    
    async def branch(self, create: Optional[str] = None, delete: Optional[str] = None,
                    list_all: bool = False, path: Optional[Path] = None) -> Dict[str, Any]:
        """Manage git branches."""
        work_dir = path or self.project_dir
        
        if create:
            command = ['branch', create]
        elif delete:
            command = ['branch', '-d', delete]
        else:
            command = ['branch']
            if list_all:
                command.append('-a')
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            command,
            cwd=work_dir
        )
        
        branches = []
        current_branch = ""
        
        if returncode == 0 and not create and not delete:
            for line in stdout.strip().split('\n'):
                if line:
                    is_current = line.startswith('*')
                    branch_name = line[2:].strip()
                    branches.append({
                        "name": branch_name,
                        "current": is_current
                    })
                    if is_current:
                        current_branch = branch_name
        
        result = {
            "success": returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
        
        if create:
            result["created"] = create
        elif delete:
            result["deleted"] = delete
        else:
            result["branches"] = branches
            result["current_branch"] = current_branch
        
        return result
    
    async def checkout(self, branch: str, create: bool = False, 
                      path: Optional[Path] = None) -> Dict[str, Any]:
        """Checkout a branch or commit."""
        work_dir = path or self.project_dir
        
        command = ['checkout']
        if create:
            command.append('-b')
        command.append(branch)
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            command,
            cwd=work_dir
        )
        
        return {
            "success": returncode == 0,
            "branch": branch,
            "created": create,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    
    async def diff(self, cached: bool = False, path: Optional[Path] = None) -> Dict[str, Any]:
        """Get git diff."""
        work_dir = path or self.project_dir
        
        command = ['diff']
        if cached:
            command.append('--cached')
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            command,
            cwd=work_dir
        )
        
        return {
            "success": returncode == 0,
            "cached": cached,
            "diff": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    
    async def remote(self, action: str = "list", name: Optional[str] = None,
                    url: Optional[str] = None, path: Optional[Path] = None) -> Dict[str, Any]:
        """Manage git remotes."""
        work_dir = path or self.project_dir
        
        if action == "add" and name and url:
            command = ['remote', 'add', name, url]
        elif action == "remove" and name:
            command = ['remote', 'remove', name]
        elif action == "get-url" and name:
            command = ['remote', 'get-url', name]
        else:
            command = ['remote', '-v']
        
        stdout, stderr, returncode = await self.git_ops.run_git_command(
            command,
            cwd=work_dir
        )
        
        remotes = []
        if returncode == 0 and action == "list":
            for line in stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        remote_name = parts[0]
                        remote_url = parts[1].split(' ')[0]
                        remotes.append({
                            "name": remote_name,
                            "url": remote_url
                        })
        
        result = {
            "success": returncode == 0,
            "action": action,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
        
        if action == "list":
            result["remotes"] = remotes
        elif action == "add":
            result["name"] = name
            result["url"] = url
        elif action == "remove":
            result["name"] = name
        
        return result