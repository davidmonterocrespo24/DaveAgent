"""
Herramientas del agente - Organizadas por categoría
"""
# Filesystem tools
from src.tools.filesystem import (
    read_file, write_file, list_dir, edit_file,
    delete_file, file_search
)

# Git tools
from src.tools.git import (
    git_status, git_add, git_commit, git_push, git_pull,
    git_log, git_branch, git_diff
)

# Data tools
from src.tools.data import (
    # JSON
    read_json, write_json, merge_json_files, validate_json,
    format_json, json_get_value, json_set_value, json_to_text,
    # CSV
    read_csv, write_csv, csv_info, filter_csv,
    merge_csv, csv_to_json, sort_csv
)

# Web tools
from src.tools.web import (
    wiki_search, wiki_summary, wiki_content,
    wiki_page_info, wiki_random, wiki_set_language
)

# Analysis tools
from src.tools.analysis import (
    analyze_python_file, find_function_definition, list_all_functions,
    codebase_search, grep_search, run_terminal_cmd, diff_history
)

__all__ = [
    # Filesystem
    "read_file", "write_file", "list_dir", "edit_file",
    "delete_file", "file_search",
    # Git
    "git_status", "git_add", "git_commit", "git_push", "git_pull",
    "git_log", "git_branch", "git_diff",
    # JSON
    "read_json", "write_json", "merge_json_files", "validate_json",
    "format_json", "json_get_value", "json_set_value", "json_to_text",
    # CSV
    "read_csv", "write_csv", "csv_info", "filter_csv",
    "merge_csv", "csv_to_json", "sort_csv",
    # Web
    "wiki_search", "wiki_summary", "wiki_content",
    "wiki_page_info", "wiki_random", "wiki_set_language",
    # Analysis
    "analyze_python_file", "find_function_definition", "list_all_functions",
    "codebase_search", "grep_search", "run_terminal_cmd", "diff_history"
]
