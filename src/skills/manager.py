"""
Skill Manager

Discovers, loads, and manages Agent Skills from configured directories.
Compatible with Claude Code skill format.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
import os

from src.skills.models import Skill
from src.skills.parser import (
    parse_skill_md,
    validate_skill_name,
    validate_skill_description,
    parse_allowed_tools,
    extract_skill_metadata,
    SkillParseError
)


class SkillManager:
    """
    Manages Agent Skills discovery, loading, and access.
    
    Scans configured directories for skill folders containing SKILL.md files,
    parses them, and provides access to skill metadata and instructions.
    
    Skill directories (in order of precedence):
    1. Personal skills: ~/.daveagent/skills/
    2. Project skills: .daveagent/skills/ (relative to working directory)
    
    Usage:
        manager = SkillManager()
        manager.discover_skills()
        
        # Get all skills
        skills = manager.get_all_skills()
        
        # Get skill by name
        pdf_skill = manager.get_skill("pdf")
        
        # Get metadata for prompt injection
        metadata = manager.get_skills_metadata()
    """
    
    # Default skill directory names
    SKILLS_DIRNAME = "skills"
    DAVEAGENT_DIRNAME = ".daveagent"
    
    def __init__(
        self,
        personal_skills_dir: Optional[Path] = None,
        project_skills_dir: Optional[Path] = None,
        additional_dirs: Optional[List[Path]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SkillManager.
        
        Args:
            personal_skills_dir: Override personal skills directory
            project_skills_dir: Override project skills directory
            additional_dirs: Additional directories to scan for skills
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Configure skill directories
        self.personal_skills_dir = personal_skills_dir or (
            Path.home() / self.DAVEAGENT_DIRNAME / self.SKILLS_DIRNAME
        )
        self.project_skills_dir = project_skills_dir or (
            Path.cwd() / self.DAVEAGENT_DIRNAME / self.SKILLS_DIRNAME
        )
        self.additional_dirs = additional_dirs or []
        
        # Skills storage (name -> Skill)
        self._skills: Dict[str, Skill] = {}
        
        # Track load errors for debugging
        self._load_errors: List[Dict] = []
    
    def discover_skills(self) -> int:
        """
        Discover and load all skills from configured directories.
        
        Returns:
            Number of skills successfully loaded
        """
        self._skills.clear()
        self._load_errors.clear()
        
        # Scan directories in order of precedence (later overrides earlier)
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
        """
        Scan a directory for skill folders.
        
        Args:
            directory: Directory to scan
            source: Source type ("personal", "project", "plugin")
        """
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
    
    def _load_skill(self, skill_path: Path, source: str) -> Optional[Skill]:
        """
        Load a skill from its directory.
        
        Args:
            skill_path: Path to skill directory
            source: Source type
            
        Returns:
            Loaded Skill or None if loading failed
        """
        skill_md_path = skill_path / "SKILL.md"
        
        try:
            # Read and parse SKILL.md
            content = skill_md_path.read_text(encoding="utf-8")
            frontmatter, body = parse_skill_md(content)
            
            # Extract and validate name
            name = str(frontmatter.get("name", "")).strip()
            is_valid, error = validate_skill_name(name)
            if not is_valid:
                raise SkillParseError(f"Invalid skill name: {error}")
            
            # Check name matches directory
            if name != skill_path.name:
                self.logger.warning(
                    f"Skill name '{name}' doesn't match directory '{skill_path.name}'"
                )
            
            # Extract and validate description
            description = str(frontmatter.get("description", "")).strip()
            is_valid, error = validate_skill_description(description)
            if not is_valid:
                raise SkillParseError(f"Invalid description: {error}")
            
            # Parse optional fields
            allowed_tools = parse_allowed_tools(frontmatter)
            license_info = frontmatter.get("license")
            metadata = extract_skill_metadata(frontmatter)
            
            # Create skill object
            skill = Skill(
                name=name,
                description=description,
                path=skill_path.absolute(),
                instructions=body,
                source=source,
                allowed_tools=allowed_tools,
                license=license_info,
                metadata=metadata
            )
            
            # Store skill (later sources override earlier)
            if name in self._skills:
                self.logger.debug(
                    f"Skill '{name}' from {source} overrides existing from "
                    f"{self._skills[name].source}"
                )
            
            self._skills[name] = skill
            self.logger.debug(f"Loaded skill: {name} from {source}")
            
            return skill
            
        except SkillParseError as e:
            self._load_errors.append({
                "path": str(skill_path),
                "error": str(e)
            })
            self.logger.warning(f"Failed to parse skill at {skill_path}: {e}")
            return None
        except Exception as e:
            self._load_errors.append({
                "path": str(skill_path),
                "error": str(e)
            })
            self.logger.error(f"Error loading skill at {skill_path}: {e}")
            return None
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name.
        
        Args:
            name: Skill name
            
        Returns:
            Skill object or None if not found
        """
        return self._skills.get(name)
    
    def get_all_skills(self) -> List[Skill]:
        """
        Get all loaded skills.
        
        Returns:
            List of all Skill objects
        """
        return list(self._skills.values())
    
    def get_skill_names(self) -> List[str]:
        """
        Get names of all loaded skills.
        
        Returns:
            List of skill names
        """
        return list(self._skills.keys())
    
    def get_skills_metadata(self) -> str:
        """
        Get formatted metadata string for all skills (for prompt injection).
        
        Returns:
            Formatted string with skill names and descriptions
        """
        if not self._skills:
            return ""
        
        lines = []
        for skill in sorted(self._skills.values(), key=lambda s: s.name):
            lines.append(skill.to_metadata_string())
        
        return "\n".join(lines)
    
    def get_skill_context(self, skill_name: str) -> Optional[str]:
        """
        Get full context string for a skill (for active skill injection).
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Formatted context string or None if skill not found
        """
        skill = self.get_skill(skill_name)
        if skill:
            return skill.to_context_string()
        return None
    
    def find_relevant_skills(
        self,
        user_query: str,
        max_results: int = 3
    ) -> List[Skill]:
        """
        Find skills relevant to a user query.
        
        Uses keyword matching on skill descriptions to find potentially
        relevant skills. More sophisticated matching could be added later
        (e.g., embedding-based similarity).
        
        Args:
            user_query: User's input/question
            max_results: Maximum number of skills to return
            
        Returns:
            List of potentially relevant skills
        """
        query_lower = user_query.lower()
        query_words = set(query_lower.split())
        
        scored_skills = []
        
        for skill in self._skills.values():
            # Simple keyword matching score
            desc_lower = skill.description.lower()
            desc_words = set(desc_lower.split())
            
            # Score based on overlapping words
            common_words = query_words & desc_words
            # Bonus for skill name appearing in query
            name_bonus = 2 if skill.name.replace("-", " ") in query_lower else 0
            
            score = len(common_words) + name_bonus
            
            if score > 0:
                scored_skills.append((score, skill))
        
        # Sort by score descending
        scored_skills.sort(key=lambda x: x[0], reverse=True)
        
        return [skill for _, skill in scored_skills[:max_results]]
    
    def get_load_errors(self) -> List[Dict]:
        """
        Get list of errors encountered during skill loading.
        
        Returns:
            List of error dictionaries with 'path' and 'error' keys
        """
        return self._load_errors.copy()
    
    def add_skills_directory(self, directory: Path, source: str = "plugin") -> int:
        """
        Add and scan an additional skills directory.
        
        Args:
            directory: Directory to scan
            source: Source type for skills in this directory
            
        Returns:
            Number of new skills loaded
        """
        before = len(self._skills)
        
        if directory.is_dir():
            self._scan_directory(directory, source)
        else:
            self.logger.warning(f"Skills directory does not exist: {directory}")
        
        return len(self._skills) - before
    
    def reload_skills(self) -> int:
        """
        Reload all skills from configured directories.
        
        Returns:
            Number of skills loaded
        """
        return self.discover_skills()
    
    def __len__(self) -> int:
        """Return number of loaded skills."""
        return len(self._skills)
    
    def __contains__(self, skill_name: str) -> bool:
        """Check if a skill is loaded."""
        return skill_name in self._skills
    
    def __iter__(self):
        """Iterate over loaded skills."""
        return iter(self._skills.values())
