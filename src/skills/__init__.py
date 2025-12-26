"""
Agent Skills Module

Implements Claude-compatible Agent Skills system for extending agent capabilities
through modular skill folders containing instructions, scripts, and resources.
"""

from src.skills.manager import SkillManager
from src.skills.models import Skill
from src.skills.parser import (
    parse_skill_body,
    parse_skill_frontmatter,
    validate_skill_description,
    validate_skill_name,
)

__all__ = [
    "Skill",
    "SkillManager",
    "parse_skill_frontmatter",
    "parse_skill_body",
    "validate_skill_name",
    "validate_skill_description",
]
