"""Tool Output Truncation with File Saving

This module implements intelligent truncation of large tool outputs to prevent
context overflow, while preserving the full content in disk for reference.

Inspired by gemini-cli's approach:
- Truncates large outputs (>40K tokens) to head (20%) + tail (80%)
- Saves full content to .claude/tool-outputs/ directory
- Provides clear indication of where to find the full output
"""

import re
from pathlib import Path

# Constants matching gemini-cli defaults
DEFAULT_TRUNCATE_THRESHOLD = 40000  # Characters (≈10K tokens)
DEFAULT_HEAD_RATIO = 0.2  # First 20% of content
DEFAULT_TAIL_RATIO = 0.8  # Last 80% of content
TOOL_OUTPUTS_DIR = "tool-outputs"


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename.

    Args:
        name: Original string

    Returns:
        Sanitized string safe for filenames

    Example:
        >>> sanitize_filename("read_file: /path/to/file.txt")
        'read_file_path_to_file_txt'
    """
    # Remove or replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    # Remove leading/trailing whitespace and dots
    safe = safe.strip(". ")
    # Limit length
    return safe[:200]


def get_tool_outputs_dir() -> Path:
    """Get the tool outputs directory, creating it if needed.

    Returns:
        Path to .claude/tool-outputs/ directory
    """
    # Create .claude directory in current workspace
    claude_dir = Path.cwd() / ".claude"
    claude_dir.mkdir(exist_ok=True)

    # Create tool-outputs subdirectory
    outputs_dir = claude_dir / TOOL_OUTPUTS_DIR
    outputs_dir.mkdir(exist_ok=True)

    return outputs_dir


async def save_tool_output(
    content: str,
    tool_name: str,
    tool_id: str,
) -> Path:
    """Save tool output to disk for later reference.

    Args:
        content: Full content to save
        tool_name: Name of the tool that produced this output
        tool_id: Unique identifier for this tool invocation

    Returns:
        Path to the saved file

    Example:
        >>> path = await save_tool_output(
        ...     large_content,
        ...     "read_file",
        ...     "001"
        ... )
        >>> print(path)
        .claude/tool-outputs/read_file_001.txt
    """
    outputs_dir = get_tool_outputs_dir()

    # Create safe filename
    safe_tool_name = sanitize_filename(tool_name).lower()
    safe_id = sanitize_filename(tool_id).lower()

    # Construct filename: tool_name_id.txt
    if safe_id.startswith(safe_tool_name):
        filename = f"{safe_id}.txt"
    else:
        filename = f"{safe_tool_name}_{safe_id}.txt"

    output_path = outputs_dir / filename

    # Write content to file
    output_path.write_text(content, encoding="utf-8")

    return output_path


def format_truncated_output(
    content: str,
    output_file: Path,
    max_chars: int = DEFAULT_TRUNCATE_THRESHOLD,
    head_ratio: float = DEFAULT_HEAD_RATIO,
    tail_ratio: float = DEFAULT_TAIL_RATIO,
) -> str:
    """Format a truncated version of content with head and tail preserved.

    Args:
        content: Original content to truncate
        output_file: Path where full content is saved
        max_chars: Maximum characters in truncated version
        head_ratio: Ratio of content to preserve from start (0.2 = 20%)
        tail_ratio: Ratio of content to preserve from end (0.8 = 80%)

    Returns:
        Formatted truncated content with file reference

    Example:
        >>> truncated = format_truncated_output(
        ...     large_content,
        ...     Path(".claude/tool-outputs/read_file_001.txt"),
        ...     max_chars=40000
        ... )
        >>> print(truncated[:100])
        Output too large. Showing first 8,000 and last 32,000 characters.
        For full output see: .claude/...
    """
    if len(content) <= max_chars:
        # Content is small enough, no truncation needed
        return content

    # Calculate head and tail sizes
    head_chars = int(max_chars * head_ratio)
    tail_chars = int(max_chars * tail_ratio)

    # Extract head and tail
    head = content[:head_chars]
    tail = content[-tail_chars:]

    # Calculate omitted section
    omitted_chars = len(content) - head_chars - tail_chars

    # Format with clear indication
    return f"""Output too large. Showing first {head_chars:,} and last {tail_chars:,} characters.
For full output see: {output_file}

{head}

... [{omitted_chars:,} characters omitted] ...

{tail}"""


async def truncate_tool_output_if_needed(
    content: str,
    tool_name: str,
    tool_id: str,
    threshold: int = DEFAULT_TRUNCATE_THRESHOLD,
) -> tuple[str, bool, Path | None]:
    """Truncate tool output if it exceeds threshold, saving full content to disk.

    This is the main entry point for tool output truncation.

    Args:
        content: Tool output content
        tool_name: Name of the tool
        tool_id: Unique ID for this tool invocation
        threshold: Character threshold for truncation

    Returns:
        Tuple of (truncated_content, was_truncated, saved_file_path)

    Example:
        >>> content, truncated, path = await truncate_tool_output_if_needed(
        ...     large_file_content,
        ...     "read_file",
        ...     "001",
        ...     threshold=40000
        ... )
        >>> if truncated:
        ...     print(f"Content saved to: {path}")
    """
    if len(content) <= threshold:
        # No truncation needed
        return content, False, None

    # Content is too large, save and truncate
    try:
        saved_path = await save_tool_output(content, tool_name, tool_id)
        truncated = format_truncated_output(content, saved_path, threshold)
        return truncated, True, saved_path
    except Exception as e:
        # If saving fails, return original content to avoid data loss
        # Log the error but don't fail the operation
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to save tool output: {e}, using original content")
        return content, False, None


def estimate_tokens(content: str) -> int:
    """Rough estimate of token count from character count.

    Uses the approximation: 1 token ≈ 4 characters

    Args:
        content: Text content

    Returns:
        Estimated token count
    """
    return len(content) // 4


def should_truncate_content(content: str, token_threshold: int = 10000) -> bool:
    """Check if content should be truncated based on token estimate.

    Args:
        content: Content to check
        token_threshold: Threshold in tokens (default: 10K tokens)

    Returns:
        True if content should be truncated
    """
    estimated_tokens = estimate_tokens(content)
    return estimated_tokens > token_threshold


# Rotation and cleanup utilities


def cleanup_old_outputs(max_files: int = 100) -> int:
    """Remove oldest tool output files if directory exceeds max_files.

    Args:
        max_files: Maximum number of files to keep

    Returns:
        Number of files deleted
    """
    outputs_dir = get_tool_outputs_dir()

    # Get all .txt files sorted by modification time
    files = sorted(outputs_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime)

    if len(files) <= max_files:
        return 0

    # Delete oldest files
    files_to_delete = files[: len(files) - max_files]
    deleted = 0

    for file_path in files_to_delete:
        try:
            file_path.unlink()
            deleted += 1
        except Exception:
            pass

    return deleted
