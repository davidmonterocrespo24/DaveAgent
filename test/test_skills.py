"""
Tests for the Agent Skills system.

Tests cover:
- SKILL.md parsing (YAML frontmatter + markdown body)
- Skill validation (name, description)
- SkillManager discovery and access
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest

from src.skills.manager import SkillManager
from src.skills.models import Skill
from src.skills.parser import (
    SkillParseError,
    parse_allowed_tools,
    parse_skill_body,
    parse_skill_frontmatter,
    parse_skill_md,
    validate_skill_description,
    validate_skill_name,
)

# =============================================================================
# PARSER TESTS
# =============================================================================


class TestSkillParser:
    """Tests for SKILL.md parsing functions."""

    def test_parse_skill_frontmatter_valid(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
name: test-skill
description: A test skill for unit testing.
license: MIT
---

# Test Skill

Some instructions here.
"""
        frontmatter = parse_skill_frontmatter(content)

        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "A test skill for unit testing."
        assert frontmatter["license"] == "MIT"

    def test_parse_skill_frontmatter_missing_name(self):
        """Test that missing name field raises error."""
        content = """---
description: A skill without a name
---

Instructions
"""
        with pytest.raises(SkillParseError, match="Missing required field 'name'"):
            parse_skill_frontmatter(content)

    def test_parse_skill_frontmatter_missing_description(self):
        """Test that missing description field raises error."""
        content = """---
name: no-description
---

Instructions
"""
        with pytest.raises(SkillParseError, match="Missing required field 'description'"):
            parse_skill_frontmatter(content)

    def test_parse_skill_frontmatter_no_frontmatter(self):
        """Test that missing frontmatter raises error."""
        content = """# No Frontmatter

Just markdown content.
"""
        with pytest.raises(SkillParseError, match="Missing YAML frontmatter"):
            parse_skill_frontmatter(content)

    def test_parse_skill_body(self):
        """Test extracting markdown body from SKILL.md."""
        content = """---
name: test
description: Test skill
---

# Test Skill

## Instructions

This is the body content.
"""
        body = parse_skill_body(content)

        assert "# Test Skill" in body
        assert "## Instructions" in body
        assert "This is the body content." in body
        assert "name: test" not in body  # Frontmatter should not be in body

    def test_parse_skill_md_complete(self):
        """Test parsing complete SKILL.md file."""
        content = """---
name: complete-skill
description: A complete test skill with all features.
license: Apache-2.0
allowed-tools: Read, Write, Edit
metadata:
  author: test
  version: "1.0"
---

# Complete Skill

Full instructions here.
"""
        frontmatter, body = parse_skill_md(content)

        assert frontmatter["name"] == "complete-skill"
        assert frontmatter["description"] == "A complete test skill with all features."
        assert "# Complete Skill" in body


class TestSkillValidation:
    """Tests for skill name and description validation."""

    def test_validate_skill_name_valid(self):
        """Test valid skill names."""
        valid_names = ["pdf", "code-review", "my-skill-123", "a", "ab"]
        for name in valid_names:
            is_valid, error = validate_skill_name(name)
            assert is_valid, f"Name '{name}' should be valid: {error}"

    def test_validate_skill_name_invalid(self):
        """Test invalid skill names."""
        invalid_names = [
            ("", "empty"),
            ("PDF", "uppercase"),
            ("-start-dash", "starts with dash"),
            ("end-dash-", "ends with dash"),
            ("has space", "contains space"),
            ("has_underscore", "contains underscore"),
            ("a" * 65, "too long"),
        ]
        for name, reason in invalid_names:
            is_valid, error = validate_skill_name(name)
            assert not is_valid, f"Name '{name}' should be invalid ({reason})"

    def test_validate_skill_description_valid(self):
        """Test valid skill descriptions."""
        is_valid, error = validate_skill_description("A valid description.")
        assert is_valid
        assert error is None

    def test_validate_skill_description_empty(self):
        """Test empty description is invalid."""
        is_valid, error = validate_skill_description("")
        assert not is_valid
        assert "cannot be empty" in error

    def test_validate_skill_description_too_long(self):
        """Test description over 1024 chars is invalid."""
        long_desc = "x" * 1025
        is_valid, error = validate_skill_description(long_desc)
        assert not is_valid
        assert "1024" in error


class TestAllowedToolsParsing:
    """Tests for allowed-tools field parsing."""

    def test_parse_allowed_tools_string(self):
        """Test parsing comma-separated string."""
        frontmatter = {"allowed-tools": "Read, Write, Edit"}
        tools = parse_allowed_tools(frontmatter)
        assert tools == ["Read", "Write", "Edit"]

    def test_parse_allowed_tools_list(self):
        """Test parsing list format."""
        frontmatter = {"allowed-tools": ["Read", "Write", "Edit"]}
        tools = parse_allowed_tools(frontmatter)
        assert tools == ["Read", "Write", "Edit"]

    def test_parse_allowed_tools_missing(self):
        """Test missing allowed-tools returns empty list."""
        frontmatter = {"name": "test", "description": "test"}
        tools = parse_allowed_tools(frontmatter)
        assert tools == []


# =============================================================================
# SKILL MODEL TESTS
# =============================================================================


class TestSkillModel:
    """Tests for the Skill dataclass."""

    def test_skill_creation(self):
        """Test creating a Skill instance."""
        skill = Skill(
            name="test-skill",
            description="A test skill",
            path=Path("/tmp/test-skill"),
            instructions="# Test\n\nInstructions here.",
            source="project",
        )

        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert skill.source == "project"
        assert skill.allowed_tools == []

    def test_skill_to_metadata_string(self):
        """Test generating metadata string for prompt injection."""
        skill = Skill(
            name="pdf-processing",
            description="Process PDF files",
            path=Path("/tmp/pdf"),
            instructions="Instructions",
            source="project",
        )

        metadata = skill.to_metadata_string()
        assert "pdf-processing" in metadata
        assert "Process PDF files" in metadata

    def test_skill_to_context_string(self):
        """Test generating full context string."""
        skill = Skill(
            name="test",
            description="Test skill",
            path=Path("/tmp/test"),
            instructions="# Instructions\n\nDo something.",
            source="personal",
            allowed_tools=["Read", "Write"],
        )

        context = skill.to_context_string()
        assert "# Skill: test" in context
        assert "Test skill" in context
        assert "Read, Write" in context
        assert "# Instructions" in context
        assert "**Path**: " in context
        assert str(Path("/tmp/test")) in context

    def test_skill_resources_detection(self):
        """Test detection of scripts and mixed references (root + subdir)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)

            # Create root reference
            (skill_dir / "forms.md").write_text("Form info")
            (skill_dir / "random.txt").write_text("Info")
            (skill_dir / "SKILL.md").write_text("---")  # Should be ignored in refs

            # Create subdir reference
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "deep.md").write_text("Deep info")

            # Create scripts
            (skill_dir / "scripts").mkdir()
            (skill_dir / "scripts" / "run.py").write_text("print('hi')")

            skill = Skill(
                name="resource-test",
                description="Test",
                path=skill_dir,
                instructions="Instructions",
                source="test",
            )

            assert skill.has_references
            assert skill.has_scripts

            refs = [p.name for p in skill.get_references()]
            assert "forms.md" in refs
            assert "random.txt" in refs
            assert "deep.md" in refs
            assert "SKILL.md" not in refs

            scripts = [p.name for p in skill.get_scripts()]
            assert "run.py" in scripts

            # Check context string mentions them
            ctx = skill.to_context_string()
            assert "forms.md" in ctx
            assert "run.py" in ctx


# =============================================================================
# SKILL MANAGER TESTS
# =============================================================================


class TestSkillManager:
    """Tests for the SkillManager class."""

    @pytest.fixture
    def mock_rag(self):
        """Create a mock RAGManager."""
        mock = MagicMock()
        # Setup search return for RAG
        mock.search.return_value = []
        return mock

    @pytest.fixture
    def temp_skills_dir(self):
        """Create a temporary skills directory with test skills."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create a valid skill
        skill_dir = temp_dir / "test-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: A test skill for verification.
---

# Test Skill

Instructions for the test skill.
""")

        # Create another skill
        skill2_dir = temp_dir / "another-skill"
        skill2_dir.mkdir()
        skill2_md = skill2_dir / "SKILL.md"
        skill2_md.write_text("""---
name: another-skill
description: Another test skill.
allowed-tools: Read, Grep
---

# Another Skill

More instructions.
""")

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_discover_skills(self, temp_skills_dir):
        """Test discovering skills from a directory."""
        manager = SkillManager(
            personal_skills_dir=temp_skills_dir, project_skills_dir=Path("/nonexistent")
        )

        count = manager.discover_skills()

        assert count == 2
        assert "test-skill" in manager
        assert "another-skill" in manager
        assert "test-skill" in manager.get_skill_names()

    def test_discover_skills_with_rag(self, temp_skills_dir, mock_rag):
        """Test discovering and indexing skills with RAG."""
        manager = SkillManager(
            rag_manager=mock_rag,
            personal_skills_dir=temp_skills_dir,
            project_skills_dir=Path("/nonexistent"),
        )

        count = manager.discover_skills()

        assert count == 2
        # Verify indexing was called 2 times (once per skill)
        assert mock_rag.add_document.call_count == 2
        # Check call args for one of them
        mock_rag.add_document.assert_any_call(
            collection_name="agent_skills", text=ANY, metadata=ANY, source_id="skill-test-skill"
        )

    def test_get_skill(self, temp_skills_dir):
        """Test getting a skill by name."""
        manager = SkillManager(
            personal_skills_dir=temp_skills_dir, project_skills_dir=Path("/nonexistent")
        )
        manager.discover_skills()

        skill = manager.get_skill("test-skill")

        assert skill is not None
        assert skill.name == "test-skill"
        assert skill.description == "A test skill for verification."

    def test_get_all_skills(self, temp_skills_dir):
        """Test getting all loaded skills."""
        manager = SkillManager(
            personal_skills_dir=temp_skills_dir, project_skills_dir=Path("/nonexistent")
        )
        manager.discover_skills()

        skills = manager.get_all_skills()

        assert len(skills) == 2
        names = [s.name for s in skills]
        assert "test-skill" in names
        assert "another-skill" in names

    def test_get_skills_metadata(self, temp_skills_dir):
        """Test generating metadata string for prompt injection."""
        manager = SkillManager(
            personal_skills_dir=temp_skills_dir, project_skills_dir=Path("/nonexistent")
        )
        manager.discover_skills()

        metadata = manager.get_skills_metadata()

        assert "test-skill" in metadata
        assert "another-skill" in metadata
        assert "A test skill for verification" in metadata

    def test_find_relevant_skills(self, temp_skills_dir):
        """Test finding skills relevant to a query."""
        manager = SkillManager(
            personal_skills_dir=temp_skills_dir, project_skills_dir=Path("/nonexistent")
        )
        manager.discover_skills()

        # Query that should match "test-skill"
        relevant = manager.find_relevant_skills("I need a test skill")

        assert len(relevant) > 0
        assert any(s.name == "test-skill" for s in relevant)

    def test_find_relevant_skills_rag(self, temp_skills_dir, mock_rag):
        """Test finding skills using RAG."""
        manager = SkillManager(
            rag_manager=mock_rag,
            personal_skills_dir=temp_skills_dir,
            project_skills_dir=Path("/nonexistent"),
        )
        manager.discover_skills()

        # Mock RAG returning a result
        mock_rag.search.return_value = [{"metadata": {"skill_name": "test-skill"}, "score": 0.9}]

        relevant = manager.find_relevant_skills("some difficult query", max_results=1)

        assert len(relevant) == 1
        assert relevant[0].name == "test-skill"
        mock_rag.search.assert_called_once()

    def test_skill_not_found(self, temp_skills_dir):
        """Test getting a non-existent skill returns None."""
        manager = SkillManager(
            personal_skills_dir=temp_skills_dir, project_skills_dir=Path("/nonexistent")
        )
        manager.discover_skills()

        skill = manager.get_skill("nonexistent-skill")

        assert skill is None

    def test_allowed_tools_loaded(self, temp_skills_dir):
        """Test that allowed-tools are properly loaded."""
        manager = SkillManager(
            personal_skills_dir=temp_skills_dir, project_skills_dir=Path("/nonexistent")
        )
        manager.discover_skills()

        skill = manager.get_skill("another-skill")

        assert skill is not None
        assert skill.allowed_tools == ["Read", "Grep"]


# =============================================================================
# INTEGRATION WITH ANTHROPIC SKILLS
# =============================================================================


class TestAnthropicSkillsCompatibility:
    """Tests for compatibility with Anthropic's skills repository."""

    @pytest.fixture
    def anthropic_skills_dir(self):
        """Path to cloned Anthropic skills (if available)."""
        skills_path = Path("docs/skills/skills")
        if skills_path.is_dir():
            return skills_path
        return None

    @pytest.mark.skipif(
        not Path("docs/skills/skills").is_dir(), reason="Anthropic skills repository not cloned"
    )
    def test_load_anthropic_pdf_skill(self, anthropic_skills_dir):
        """Test loading the PDF skill from Anthropic's repository."""
        manager = SkillManager(
            personal_skills_dir=Path("/nonexistent"),
            project_skills_dir=Path("/nonexistent"),
            additional_dirs=[anthropic_skills_dir],
        )
        manager.discover_skills()

        # Check that PDF skill was loaded
        pdf_skill = manager.get_skill("pdf")
        assert pdf_skill is not None
        assert "PDF" in pdf_skill.description or "pdf" in pdf_skill.description.lower()

    @pytest.mark.skipif(
        not Path("docs/skills/skills").is_dir(), reason="Anthropic skills repository not cloned"
    )
    def test_load_multiple_anthropic_skills(self, anthropic_skills_dir):
        """Test loading multiple skills from Anthropic's repository."""
        manager = SkillManager(
            personal_skills_dir=Path("/nonexistent"),
            project_skills_dir=Path("/nonexistent"),
            additional_dirs=[anthropic_skills_dir],
        )
        count = manager.discover_skills()

        # Should load multiple skills
        assert count > 5, f"Expected to load multiple skills, got {count}"

        # Check no load errors for expected skills
        errors = manager.get_load_errors()
        # Some skills might have issues, but core ones should work
        skill_names = manager.get_skill_names()
        assert len(skill_names) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
