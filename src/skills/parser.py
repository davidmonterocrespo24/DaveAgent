"""
SKILL.md Parser

Utilities for parsing SKILL.md files with YAML frontmatter and markdown body.
Compatible with Claude Code skill format.
"""

import re
from typing import Any

import yaml

# Regex pattern for YAML frontmatter
FRONTMATTER_PATTERN = re.compile(
    r'^---\s*\n(.*?)\n---\s*\n?',
    re.DOTALL
)

# Skill name validation pattern (lowercase alphanumeric + hyphens)
SKILL_NAME_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$')

# Maximum lengths
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024


class SkillParseError(Exception):
    """Raised when SKILL.md parsing fails."""
    pass


def parse_skill_frontmatter(content: str) -> dict[str, Any]:
    """
    Extract and parse YAML frontmatter from SKILL.md content.
    
    Args:
        content: Full content of SKILL.md file
        
    Returns:
        Dictionary with parsed frontmatter fields
        
    Raises:
        SkillParseError: If frontmatter is missing or invalid YAML
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        raise SkillParseError(
            "Invalid SKILL.md format: Missing YAML frontmatter. "
            "File must start with '---' followed by YAML and closing '---'."
        )

    yaml_content = match.group(1)

    try:
        frontmatter = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise SkillParseError(f"Invalid YAML in frontmatter: {e}")

    if not isinstance(frontmatter, dict):
        raise SkillParseError("Frontmatter must be a YAML mapping (key: value pairs)")

    # Validate required fields
    if 'name' not in frontmatter:
        raise SkillParseError("Missing required field 'name' in frontmatter")
    if 'description' not in frontmatter:
        raise SkillParseError("Missing required field 'description' in frontmatter")

    return frontmatter


def parse_skill_body(content: str) -> str:
    """
    Extract markdown body from SKILL.md content (everything after frontmatter).
    
    Args:
        content: Full content of SKILL.md file
        
    Returns:
        Markdown body content trimmed of leading/trailing whitespace
    """
    match = FRONTMATTER_PATTERN.match(content)
    if match:
        # Return everything after the frontmatter
        body = content[match.end():]
        return body.strip()
    else:
        # No frontmatter found, return entire content
        return content.strip()


def parse_skill_md(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse complete SKILL.md file into frontmatter and body.
    
    Args:
        content: Full content of SKILL.md file
        
    Returns:
        Tuple of (frontmatter_dict, body_markdown)
        
    Raises:
        SkillParseError: If parsing fails
    """
    frontmatter = parse_skill_frontmatter(content)
    body = parse_skill_body(content)
    return frontmatter, body


def validate_skill_name(name: str) -> tuple[bool, str | None]:
    """
    Validate skill name according to specification.
    
    Rules:
    - Lowercase Unicode alphanumeric + hyphen only
    - Cannot start or end with hyphen
    - Maximum 64 characters
    
    Args:
        name: Skill name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid
    """
    if not name:
        return False, "Skill name cannot be empty"

    if len(name) > MAX_NAME_LENGTH:
        return False, f"Skill name exceeds maximum length of {MAX_NAME_LENGTH} characters"

    if not SKILL_NAME_PATTERN.match(name):
        return False, (
            "Skill name must use only lowercase letters, numbers, and hyphens. "
            "Cannot start or end with a hyphen."
        )

    return True, None


def validate_skill_description(description: str) -> tuple[bool, str | None]:
    """
    Validate skill description according to specification.
    
    Rules:
    - Cannot be empty
    - Maximum 1024 characters
    
    Args:
        description: Skill description to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid
    """
    if not description:
        return False, "Skill description cannot be empty"

    if len(description) > MAX_DESCRIPTION_LENGTH:
        return False, f"Skill description exceeds maximum length of {MAX_DESCRIPTION_LENGTH} characters"

    return True, None


def parse_allowed_tools(frontmatter: dict[str, Any]) -> list:
    """
    Parse allowed-tools field from frontmatter.
    
    Handles both string format ("Read, Write, Edit") and list format.
    
    Args:
        frontmatter: Parsed frontmatter dictionary
        
    Returns:
        List of tool names
    """
    allowed = frontmatter.get('allowed-tools', [])

    if isinstance(allowed, str):
        # Parse comma-separated string
        return [tool.strip() for tool in allowed.split(',') if tool.strip()]
    elif isinstance(allowed, list):
        return [str(tool).strip() for tool in allowed if tool]
    else:
        return []


def extract_skill_metadata(frontmatter: dict[str, Any]) -> dict[str, str]:
    """
    Extract custom metadata from frontmatter.
    
    Args:
        frontmatter: Parsed frontmatter dictionary
        
    Returns:
        Dictionary of custom metadata (string key-value pairs)
    """
    metadata = frontmatter.get('metadata', {})
    if isinstance(metadata, dict):
        # Convert all values to strings
        return {str(k): str(v) for k, v in metadata.items()}
    return {}
