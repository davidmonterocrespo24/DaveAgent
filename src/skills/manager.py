"""
Skill Manager

Discovers, loads, and manages Agent Skills from configured directories.
Compatible with Claude Code skill format.
Uses RAG for semantic skill discovery.
"""

import logging
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
    parses them, and provides access to skill metadata and instructions.
    
    Uses RAG (Retrieval-Augmented Generation) to semantic search for relevant
    skills based on user queries, ensuring efficient context usage.
    
    Skill directories (in order of precedence):
    1. Personal skills: ~/.daveagent/skills/
    2. Project skills: .daveagent/skills/ (relative to working directory)
    """

    # Default skill directory names
    SKILLS_DIRNAME = "skills"
    DAVEAGENT_DIRNAME = ".daveagent"
    RAG_COLLECTION = "agent_skills"

    def __init__(
        self,
        rag_manager=None,
        personal_skills_dir: Path | None = None,
        project_skills_dir: Path | None = None,
        additional_dirs: list[Path] | None = None,
        logger: logging.Logger | None = None
    ):
        """
        Initialize the SkillManager.
        
        Args:
            rag_manager: RAGManager instance for skill indexing/retrieval
            personal_skills_dir: Override personal skills directory
            project_skills_dir: Override project skills directory
            additional_dirs: Additional directories to scan for skills
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.rag_manager = rag_manager

        # Configure skill directories
        self.personal_skills_dir = personal_skills_dir or (
            Path.home() / self.DAVEAGENT_DIRNAME / self.SKILLS_DIRNAME
        )
        self.project_skills_dir = project_skills_dir or (
            Path.cwd() / self.DAVEAGENT_DIRNAME / self.SKILLS_DIRNAME
        )
        self.additional_dirs = additional_dirs or []

        # Skills storage (name -> Skill)
        self._skills: dict[str, Skill] = {}

        # Track load errors for debugging
        self._load_errors: list[dict] = []

    def discover_skills(self) -> int:
        """
        Discover, load, and index all skills from configured directories.
        
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

        # 1. Load all skills into memory
        for skill_dir, source in directories:
            if skill_dir.is_dir():
                self._scan_directory(skill_dir, source)
            else:
                self.logger.debug(f"Skill directory does not exist: {skill_dir}")

        # 2. Index skills in RAG if manager available
        if self.rag_manager and self._skills:
            self._index_skills()

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
                metadata=extract_skill_metadata(frontmatter)
            )

            self._skills[name] = skill
            return skill

        except Exception as e:
            self._load_errors.append({"path": str(skill_path), "error": str(e)})
            self.logger.warning(f"Failed to load skill at {skill_path}: {e}")
            return None

    def _index_skills(self):
        """Index loaded skills into RAG system for semantic retrieval."""
        try:
            # Load existing hashes to check for changes
            hashes = self._load_hashes()
            new_hashes = {}
            skills_to_index = []
            skipped_count = 0

            for skill in self._skills.values():
                # Content includes description and full instructions for matching
                search_content = f"Skill: {skill.name}\nDescription: {skill.description}\n\n{skill.instructions}"

                # Deterministic ID based on skill name
                source_id = f"skill-{skill.name}"

                # Compute hash of the content
                import hashlib
                content_hash = hashlib.md5(search_content.encode("utf-8")).hexdigest()
                new_hashes[source_id] = content_hash

                # Check if changed
                if source_id in hashes and hashes[source_id] == content_hash:
                    skipped_count += 1
                    self.logger.debug(f"Skipping indexing for unchanging skill: {skill.name}")
                    continue

                metadata = {
                    "skill_name": skill.name,
                    "source": skill.source,
                    "type": "agent_skill"
                }

                skills_to_index.append({
                    "collection_name": self.RAG_COLLECTION,
                    "text": search_content,
                    "metadata": metadata,
                    "source_id": source_id
                })

            # Perform indexing only for new/changed skills
            if skills_to_index:
                self.logger.info(f"Indexing {len(skills_to_index)} new/modified skills in RAG...")
                for item in skills_to_index:
                    self.rag_manager.add_document(**item)

            if skipped_count > 0:
                self.logger.info(f"Skipped {skipped_count} unchanged skills")

            # Save new hashes if we successfully processed everything
            self._save_hashes(new_hashes)

            self.logger.info("✓ Skills indexing completed")

        except Exception as e:
            self.logger.error(f"Error indexing skills: {e}")

    def _get_hashes_file(self) -> Path:
        """Get path to skills hash file."""
        return self.personal_skills_dir.parent / "skills_hashes.json"

    def _load_hashes(self) -> dict[str, str]:
        """Load stored skill hashes."""
        hash_file = self._get_hashes_file()
        if not hash_file.exists():
            return {}
        try:
            import json
            return json.loads(hash_file.read_text(encoding="utf-8"))
        except Exception as e:
            self.logger.warning(f"Failed to load skill hashes: {e}")
            return {}

    def _save_hashes(self, hashes: dict[str, str]):
        """Save skill hashes."""
        try:
            import json
            hash_file = self._get_hashes_file()
            # Ensure directory exists (it should, but just in case)
            hash_file.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(hashes, indent=2)
            hash_file.write_text(text, encoding="utf-8")
        except Exception as e:
            self.logger.error(f"Failed to save skill hashes: {e}")


    def find_relevant_skills(self, user_query: str, max_results: int = 10, min_score: float = 0.5) -> list[Skill]:
        """
        Find skills relevant to a user query using RAG semantic search.
        Falls back to keyword matching if RAG is not available.

        Args:
            user_query: User's input/question
            max_results: Maximum number of skills to return
            min_score: Minimum relevance score (0.0-1.0). Recommended: 0.5 for skills
                      to avoid false positives. Only skills with score >= min_score
                      will be returned.

        Returns:
            List of relevant Skill objects, sorted by relevance
        """
        if not self._skills:
            return []

        # 1. Use RAG if available
        if self.rag_manager:
            try:
                results = self.rag_manager.search(
                    collection_name=self.RAG_COLLECTION,
                    query=user_query,
                    top_k=max_results,
                    min_score=min_score  # Umbral de relevancia
                )

                found_skills = []
                seen_names = set()

                for res in results:
                    # Get skill name from metadata if available, or infer from id
                    meta = res.get('metadata', {})
                    skill_name = meta.get('skill_name')
                    score = res.get('score', 0.0)

                    # If not in metadata (e.g. child chunk), parsed from content or fallback
                    if not skill_name and 'skill-' in str(res.get('id', '')):
                        # Try to extract from ID logic (skill-name-...)
                        # But simpler: just look up in our loaded skills which one matches
                        pass

                    if skill_name and skill_name in self._skills and skill_name not in seen_names:
                        found_skills.append(self._skills[skill_name])
                        seen_names.add(skill_name)
                        self.logger.debug(f"  - Skill '{skill_name}' matched with score {score:.4f}")

                if found_skills:
                    self.logger.info(f"RAG found {len(found_skills)} relevant skill(s) with score >= {min_score}")
                    return found_skills
                else:
                    self.logger.debug(f"RAG found no skills with score >= {min_score}")
                    return []

            except Exception as e:
                # Log detallado del error real para debugging
                import traceback
                self.logger.debug(f"RAG search exception: {type(e).__name__}: {e}")
                self.logger.debug(f"Traceback: {traceback.format_exc()}")
                # Solo mostrar warning si es un error inesperado (no por falta de resultados)
                if "index out of range" not in str(e).lower():
                    self.logger.warning(f"RAG skill search failed: {e}. Falling back to keywords.")
                else:
                    self.logger.debug(f"RAG search returned no results, using keyword fallback.")

        # 2. Keywork fallback (or if RAG returned nothing/failed)
        return self._find_skills_by_keyword(user_query, max_results)

    def _find_skills_by_keyword(self, user_query: str, max_results: int) -> list[Skill]:
        """Simple keyword matching fallback."""
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

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------

    def get_skill(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def get_all_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def get_skills_metadata(self) -> str:
        """Get list of ALL skills metadata (legacy/fallback usage)."""
        if not self._skills: return ""
        lines = [s.to_metadata_string() for s in sorted(self._skills.values(), key=lambda s: s.name)]
        return "\n".join(lines)

    def get_skill_context(self, skill_name: str) -> str | None:
        skill = self.get_skill(skill_name)
        return skill.to_context_string() if skill else None

    def get_skill_names(self) -> list[str]:
        """Get names of all loaded skills."""
        return list(self._skills.keys())

    def get_load_errors(self) -> list[dict]:
        return self._load_errors.copy()

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, item: str) -> bool:
        return item in self._skills

