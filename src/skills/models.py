"""
Skill Data Models

Defines the Skill dataclass representing an Agent Skill.
Compatible with Claude Code skill format.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class Skill:
    """
    Represents an Agent Skill.
    
    Skills are modular capabilities that extend agent functionality through
    organized folders containing instructions, scripts, and resources.
    
    Attributes:
        name: Skill identifier in hyphen-case (e.g., "pdf-processing")
        description: What the skill does and when to use it (max 1024 chars)
        path: Absolute path to the skill directory
        instructions: Markdown body from SKILL.md with detailed guidance
        allowed_tools: Optional list of pre-approved tools for this skill
        license: Optional license information
        metadata: Optional custom key-value pairs
        source: Origin of the skill ("personal", "project", or "plugin")
    """
    name: str
    description: str
    path: Path
    instructions: str
    source: str
    allowed_tools: List[str] = field(default_factory=list)
    license: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure path is a Path object."""
        if isinstance(self.path, str):
            self.path = Path(self.path)
    
    @property
    def has_scripts(self) -> bool:
        """Check if skill has a scripts directory."""
        return (self.path / "scripts").is_dir()
    
    @property
    def has_references(self) -> bool:
        """Check if skill has reference files (in root or references/ subdir)."""
        if not self.path.is_dir():
            return False
            
        if (self.path / "references").is_dir():
            return True
        # Check for root level md/txt files (excluding SKILL.md, LICENSE)
        for item in self.path.iterdir():
            if item.is_file() and item.suffix.lower() in ['.md', '.txt']:
                if item.name.lower() not in ['skill.md', 'license.txt', 'license']:
                    return True
        return False
    
    @property
    def has_assets(self) -> bool:
        """Check if skill has an assets directory."""
        return (self.path / "assets").is_dir()
    
    def get_scripts(self) -> List[Path]:
        """Get list of script files in the skill."""
        scripts_dir = self.path / "scripts"
        if scripts_dir.is_dir():
            return list(scripts_dir.iterdir())
        return []
    
    def get_references(self) -> List[Path]:
        """Get list of reference files in the skill."""
        if not self.path.is_dir():
            return []
            
        refs = []
        
        # 1. references/ subdirectory
        refs_dir = self.path / "references"
        if refs_dir.is_dir():
            refs.extend(list(refs_dir.iterdir()))
            
        # 2. Root level documentation
        for item in self.path.iterdir():
            if item.is_file() and item.suffix.lower() in ['.md', '.txt']:
                if item.name.lower() not in ['skill.md', 'license.txt', 'license']:
                    refs.append(item)
                    
        return sorted(list(set(refs)), key=lambda p: p.name)
    
    def get_reference_content(self, filename: str) -> Optional[str]:
        """
        Read content of a reference file.
        
        Args:
            filename: Name of the reference file (e.g., "forms.md")
            
        Returns:
            File content as string, or None if file doesn't exist
        """
        ref_path = self.path / "references" / filename
        if ref_path.is_file():
            return ref_path.read_text(encoding="utf-8")
        # Also check without references/ prefix
        ref_path = self.path / filename
        if ref_path.is_file():
            return ref_path.read_text(encoding="utf-8")
        return None
    
    def to_metadata_string(self) -> str:
        """
        Generate metadata string for prompt injection.
        
        Returns:
            Formatted string with skill name and description
        """
        return f"- **{self.name}**: {self.description}"
    
    def to_context_string(self) -> str:
        """
        Generate full context string for active skill injection.
        
        Returns:
            Formatted string with skill name, description, and instructions
        """
        context = f"# Skill: {self.name}\n\n"
        context += f"**Description**: {self.description}\n"
        context += f"**Path**: {self.path}\n\n"
        
        if self.allowed_tools:
            context += f"**Allowed Tools**: {', '.join(self.allowed_tools)}\n\n"
        
        context += f"## Instructions\n\n{self.instructions}"
        
        # Add info about available resources
        resources = []
        if self.has_scripts:
            scripts = [s.name for s in self.get_scripts()]
            resources.append(f"Scripts: {', '.join(scripts)}")
        if self.has_references:
            refs = [r.name for r in self.get_references()]
            resources.append(f"References: {', '.join(refs)}")
        if self.has_assets:
            resources.append("Assets: Available in assets/ directory")
        
        if resources:
            context += f"\n\n## Available Resources\n"
            for res in resources:
                context += f"- {res}\n"
        
        return context
    
    def __repr__(self) -> str:
        return f"Skill(name='{self.name}', source='{self.source}', path='{self.path}')"
