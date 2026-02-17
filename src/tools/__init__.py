"""
Agent tools - Organized by category
"""

# Analysis tools
from src.tools.code_analyzer import (
    analyze_python_file,
    find_function_definition,
    list_all_functions,
)
from src.tools.csv_tools import (
    csv_info,
    csv_to_json,
    filter_csv,
    merge_csv_files,
    read_csv,
    sort_csv,
    write_csv,
)
from src.tools.delete_file import delete_file
from src.tools.directory_ops import list_dir
from src.tools.edit_file import edit_file

# Git tools
from src.tools.git_operations import (
    git_add,
    git_branch,
    git_commit,
    git_diff,
    git_log,
    git_pull,
    git_push,
    git_status,
)
from src.tools.glob import glob_search
from src.tools.grep import grep_search

# Data tools
from src.tools.json_tools import (
    format_json,
    json_get_value,
    json_set_value,
    json_to_text,
    merge_json_files,
    read_json,
    validate_json,
    write_json,
)

# Filesystem tools
from src.tools.read_file import read_file
from src.tools.search_file import file_search

# Subagent tools
from src.tools.spawn_subagent import spawn_subagent
from src.tools.check_subagent_results import check_subagent_results
from src.tools.terminal import run_terminal_cmd
from src.tools.web_search import web_search

# Web tools
from src.tools.wikipedia_tools import (
    wiki_content,
    wiki_page_info,
    wiki_random,
    wiki_search,
    wiki_set_language,
    wiki_summary,
)
from src.tools.write_file import write_file

__all__ = [
    # Filesystem
    "read_file",
    "write_file",
    "list_dir",
    "edit_file",
    "delete_file",
    "file_search",
    "glob_search",
    # Git
    "git_status",
    "git_add",
    "git_commit",
    "git_push",
    "git_pull",
    "git_log",
    "git_branch",
    "git_diff",
    # JSON
    "read_json",
    "write_json",
    "merge_json_files",
    "validate_json",
    "format_json",
    "json_get_value",
    "json_set_value",
    "json_to_text",
    # CSV
    "read_csv",
    "write_csv",
    "csv_info",
    "filter_csv",
    "merge_csv",
    "csv_to_json",
    "sort_csv",
    # Web
    "wiki_search",
    "wiki_summary",
    "wiki_content",
    "wiki_page_info",
    "wiki_random",
    "wiki_set_language",
    "web_search",
    # Analysis
    "analyze_python_file",
    "find_function_definition",
    "list_all_functions",
    "grep_search",
    "run_terminal_cmd",
    # Subagents
    "spawn_subagent",
    "check_subagent_results",
]
