"""
Skill Manager

Discovers and loads Agent Skills from configured directories.
Compatible with Claude Code skill format.
Skills are matched by keyword search on their descriptions.
"""

import logging
import os
import shutil
from pathlib import Path

from src.skills.models import Skill
from src.skills.parser import (
    SkillParseError,
    extract_skill_metadata,
    parse_allowed_tools,
    parse_skill_md,
    validate_skill_description,
    validate_skill_name,
)


class SkillManager:
    """
    Manages Agent Skills discovery, loading, and access.

    Scans configured directories for skill folders containing SKILL.md files,
    parses them, and provides keyword-based skill discovery.

    Skill directories (in order of precedence):
    1. Personal skills: ~/.daveagent/skills/
    2. Project skills: .daveagent/skills/ (relative to working directory)
    """

    SKILLS_DIRNAME = "skills"
    DAVEAGENT_DIRNAME = ".daveagent"

    def __init__(
        self,
        personal_skills_dir: Path | None = None,
        project_skills_dir: Path | None = None,
        additional_dirs: list[Path] | None = None,
        logger: logging.Logger | None = None,
        # kept for backwards compat - ignored
        rag_manager=None,
    ):
        self.logger = logger or logging.getLogger(__name__)

        self.personal_skills_dir = personal_skills_dir or (
            Path.home() / self.DAVEAGENT_DIRNAME / self.SKILLS_DIRNAME
        )
        self.project_skills_dir = project_skills_dir or (
            Path.cwd() / self.DAVEAGENT_DIRNAME / self.SKILLS_DIRNAME
        )
        self.additional_dirs = additional_dirs or []

        self._skills: dict[str, Skill] = {}
        self._load_errors: list[dict] = []

    def discover_skills(self) -> int:
        """
        Discover and load all skills from configured directories.

        Returns:
            Number of skills successfully loaded
        """
        self._skills.clear()
        self._load_errors.clear()

        directories = [
            (self.personal_skills_dir, "personal"),
            (self.project_skills_dir, "project"),
        ]
        for additional_dir in self.additional_dirs:
            directories.append((additional_dir, "plugin"))

        for skill_dir, source in directories:
            if skill_dir.is_dir():
                self._scan_directory(skill_dir, source)
            else:
                self.logger.debug(f"Skill directory does not exist: {skill_dir}")

        self.logger.info(f"Discovered {len(self._skills)} skills")
        if self._load_errors:
            self.logger.warning(f"Failed to load {len(self._load_errors)} skills")

        return len(self._skills)

    def _scan_directory(self, directory: Path, source: str) -> None:
        """Scan a directory for skill folders."""
        self.logger.debug(f"Scanning for skills in: {directory}")
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    skill_md = item / "SKILL.md"
                    if skill_md.is_file():
                        self._load_skill(item, source)
        except PermissionError as e:
            self.logger.warning(f"Permission denied scanning {directory}: {e}")
        except Exception as e:
            self.logger.error(f"Error scanning {directory}: {e}")

    def _load_skill(self, skill_path: Path, source: str) -> Skill | None:
        """Load a skill from its directory."""
        skill_md_path = skill_path / "SKILL.md"
        try:
            content = skill_md_path.read_text(encoding="utf-8")
            frontmatter, body = parse_skill_md(content)

            name = str(frontmatter.get("name", "")).strip()
            is_valid, error = validate_skill_name(name)
            if not is_valid:
                raise SkillParseError(f"Invalid skill name: {error}")

            description = str(frontmatter.get("description", "")).strip()
            is_valid, error = validate_skill_description(description)
            if not is_valid:
                raise SkillParseError(f"Invalid description: {error}")

            skill = Skill(
                name=name,
                description=description,
                path=skill_path.absolute(),
                instructions=body,
                source=source,
                allowed_tools=parse_allowed_tools(frontmatter),
                license=frontmatter.get("license"),
                metadata=extract_skill_metadata(frontmatter),
            )

            self._skills[name] = skill
            return skill

        except Exception as e:
            self._load_errors.append({"path": str(skill_path), "error": str(e)})
            self.logger.warning(f"Failed to load skill at {skill_path}: {e}")
            return None

    def find_relevant_skills(
        self, user_query: str, max_results: int = 10, min_score: float = 0.0
    ) -> list[Skill]:
        """
        Find skills relevant to a user query using keyword matching on descriptions.

        Args:
            user_query: User's input/question
            max_results: Maximum number of skills to return
            min_score: Minimum keyword match score (ignored if 0)

        Returns:
            List of relevant Skill objects, sorted by relevance
        """
        if not self._skills:
            return []
        return self._find_skills_by_keyword(user_query, max_results)

    def _find_skills_by_keyword(self, user_query: str, max_results: int) -> list[Skill]:
        """Keyword matching on skill name and description."""
        query_lower = user_query.lower()
        query_words = set(query_lower.split())
        scored_skills = []

        for skill in self._skills.values():
            desc_lower = skill.description.lower()
            desc_words = set(desc_lower.split())
            common = query_words & desc_words
            name_bonus = 2 if skill.name.replace("-", " ") in query_lower else 0
            score = len(common) + name_bonus

            if score > 0:
                scored_skills.append((score, skill))

        scored_skills.sort(key=lambda x: x[0], reverse=True)
        return [skill for _, skill in scored_skills[:max_results]]

    def build_skills_summary(self) -> str:
        """
        Build an XML summary of all skills (name + description only).
        Used for agent context injection - no full instructions loaded.

        Returns:
            XML-formatted skills summary
        """
        if not self._skills:
            return ""

        def escape_xml(s: str) -> str:
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        lines = ["<skills>"]
        for skill in sorted(self._skills.values(), key=lambda s: s.name):
            name = escape_xml(skill.name)
            desc = escape_xml(skill.description)
            path = str(skill.path)
            lines.append(f"  <skill>")
            lines.append(f"    <name>{name}</name>")
            lines.append(f"    <description>{desc}</description>")
            lines.append(f"    <location>{path}</location>")
            lines.append(f"  </skill>")
        lines.append("</skills>")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------

    def get_skill(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def get_all_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def get_skills_metadata(self) -> str:
        """Get list of ALL skills as metadata strings."""
        if not self._skills:
            return ""
        lines = [
            s.to_metadata_string() for s in sorted(self._skills.values(), key=lambda s: s.name)
        ]
        return "\n".join(lines)

    def get_skill_context(self, skill_name: str) -> str | None:
        skill = self.get_skill(skill_name)
        return skill.to_context_string() if skill else None

    def get_skill_names(self) -> list[str]:
        return list(self._skills.keys())

    def get_load_errors(self) -> list[dict]:
        return self._load_errors.copy()

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, item: str) -> bool:
        return item in self._skills
