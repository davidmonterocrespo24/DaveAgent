"""
Herramientas del agente - Organizadas por categoría
"""

# Filesystem tools
from src.tools.read_file import read_file
from src.tools.write_file import write_file
from src.tools.directory_ops import list_dir
from src.tools.edit_file import edit_file
from src.tools.delete_file import delete_file
from src.tools.search_file import file_search
from src.tools.glob_tool import glob_search

# Git tools
from src.tools.git_operations import (
    git_status, git_add, git_commit, git_push, git_pull,
    git_log, git_branch, git_diff
)

# Data tools
from src.tools.json_tools import (
    read_json, write_json, merge_json_files, validate_json,
    format_json, json_get_value, json_set_value, json_to_text
)
from src.tools.csv_tools import (
    read_csv, write_csv, csv_info, filter_csv,
    merge_csv, csv_to_json, sort_csv
)

# Web tools
from src.tools.wikipedia_tools import (
    wiki_search, wiki_summary, wiki_content,
    wiki_page_info, wiki_random, wiki_set_language
)
from src.tools.web_search import web_search

# Analysis tools
from src.tools.code_analyzer import (
    analyze_python_file, find_function_definition, list_all_functions
)
from src.tools.search_tools import (
    grep_search, run_terminal_cmd
)

# Memory tools (RAG-based)
from src.tools.memory_tools import (
    query_conversation_memory, query_codebase_memory,
    query_decision_memory, query_preferences_memory,
    query_user_memory, save_user_info,
    save_decision, save_preference,
    set_memory_manager
)

__all__ = [
    # Filesystem
    "read_file", "write_file", "list_dir", "edit_file",
    "delete_file", "file_search", "glob_search",
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
    "web_search",
    # Analysis
    "analyze_python_file", "find_function_definition", "list_all_functions",
    "grep_search", "run_terminal_cmd",
    # Memory (RAG)
    "query_conversation_memory", "query_codebase_memory",
    "query_decision_memory", "query_preferences_memory",
    "query_user_memory", "save_user_info",
    "save_decision", "save_preference",
    "set_memory_manager"
]
