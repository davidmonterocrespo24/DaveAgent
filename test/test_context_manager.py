import shutil
import tempfile
import unittest
from pathlib import Path

from src.managers.context_manager import ContextManager


class TestContextManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = ContextManager()
        # Override home for testing
        self.manager.home_context_path = self.test_dir / ".daveagent" / "DAVEAGENT.md"
        self.manager.home_context_path.parent.mkdir(exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_create_template(self):
        target_dir = self.test_dir / "project"
        target_dir.mkdir()

        path = self.manager.create_template(target_dir)

        self.assertTrue(path.exists())
        self.assertEqual(path.name, "DAVEAGENT.md")
        content = path.read_text(encoding="utf-8")
        self.assertIn("# DAVEAGENT.md", content)

    def test_discover_context_files(self):
        # Create a mock structure
        # /
        #   .daveagent/DAVEAGENT.md (Home)
        #   project/
        #     DAVEAGENT.md (Parent)
        #     subdir/
        #       (Current)

        # 1. Setup Home
        self.manager.home_context_path.write_text("HOME CONTEXT")

        # 2. Setup Project
        project_dir = self.test_dir / "project"
        project_dir.mkdir()
        project_context = project_dir / "DAVEAGENT.md"
        project_context.write_text("PROJECT CONTEXT")

        # 3. Setup Subdir
        sub_dir = project_dir / "subdir"
        sub_dir.mkdir()

        # Mocking cwd is tricky in unit tests without changing global state
        # So we'll trust the logic or use os.chdir context manager if needed,
        # but for now let's test specific logic by temporarily changing cwd
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(sub_dir)

            # Re-initialize to pick up relative paths if any (though logic uses absolute)
            # manager = ContextManager()
            # We need to manually inject our fake home path again if we re-init
            # But the existing manager instance should work if logic is robust

            files = self.manager.discover_context_files()

            # Should find Home and Project
            self.assertEqual(len(files), 2)
            self.assertEqual(files[0], self.manager.home_context_path)
            self.assertEqual(files[1].resolve(), project_context.resolve())

        finally:
            import os

            os.chdir(original_cwd)

    def test_get_combined_context(self):
        # Setup similar to above
        self.manager.home_context_path.write_text("HOME")

        project_dir = self.test_dir / "project"
        project_dir.mkdir()
        project_context = project_dir / "DAVEAGENT.md"
        project_context.write_text("PROJECT")

        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(project_dir)

            combined = self.manager.get_combined_context()

            self.assertIn("<project_context>", combined)
            self.assertIn("--- SOURCE:", combined)
            self.assertIn("HOME", combined)
            self.assertIn("PROJECT", combined)

        finally:
            import os

            os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
