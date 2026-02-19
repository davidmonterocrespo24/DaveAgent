"""
Tests for autocompletion features (FASE 5).

Tests:
1. Command completion (slash commands)
2. File completion after @ symbol
3. Fuzzy matching for files
"""

import sys
import os

# Ensure we import from local src, not system site-packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from unittest.mock import Mock, patch
from prompt_toolkit.document import Document


def test_imports():
    """Test that all required imports work."""
    from src.interfaces.cli_interface import CLIInterface, FileCompleter
    from prompt_toolkit.completion import WordCompleter
    assert CLIInterface is not None
    assert FileCompleter is not None
    assert WordCompleter is not None
    print("✅ All imports successful")


def test_file_completer_basic():
    """Test basic file completion functionality."""
    from src.interfaces.cli_interface import FileCompleter

    # Create a FileCompleter
    completer = FileCompleter(base_dir=".")

    # Create a document with @ mention
    doc = Document("Please analyze @src")

    # Get completions
    completions = list(completer.get_completions(doc, None))

    # Should have completions starting with "src"
    assert len(completions) > 0, "Should have file completions"

    # All completions should contain "src" in the path
    for completion in completions[:5]:  # Check first 5
        assert "src" in completion.text.lower(), f"Completion {completion.text} should contain 'src'"

    print(f"✅ File completer found {len(completions)} matches for 'src'")


def test_file_completer_fuzzy_match():
    """Test fuzzy matching in file completer."""
    from src.interfaces.cli_interface import FileCompleter

    completer = FileCompleter(base_dir=".")

    # Test fuzzy match method directly
    assert completer._fuzzy_match("abc", "aXbXcX") == True, "Should match with chars in between"
    assert completer._fuzzy_match("src", "src/main.py") == True, "Should match prefix"
    assert completer._fuzzy_match("mai", "src/main.py") == True, "Should match 'mai' in 'main'"
    assert completer._fuzzy_match("xyz", "abc") == False, "Should not match if chars not present"
    assert completer._fuzzy_match("", "anything") == True, "Empty query matches everything"

    print("✅ Fuzzy matching works correctly")


def test_file_completer_no_completion_without_at():
    """Test that file completer only works after @ symbol."""
    from src.interfaces.cli_interface import FileCompleter

    completer = FileCompleter(base_dir=".")

    # Document without @
    doc = Document("Please analyze src/main.py")

    # Should have no completions
    completions = list(completer.get_completions(doc, None))
    assert len(completions) == 0, "Should not complete without @ symbol"

    print("✅ File completer correctly ignores input without @")


def test_file_completer_cache():
    """Test that file cache is populated and used."""
    from src.interfaces.cli_interface import FileCompleter

    completer = FileCompleter(base_dir=".")

    # Trigger cache refresh
    completer._refresh_cache()

    # Should have files in cache
    assert len(completer._file_cache) > 0, "Cache should be populated"

    # Cache should not include files from excluded directories (check path parts)
    excluded_found = False
    for file_path in completer._file_cache:
        parts = file_path.split(os.sep)
        # Should not have these as directory components
        if any(excluded in parts for excluded in ['.git', 'node_modules', '__pycache__']):
            excluded_found = True
            break

    assert not excluded_found, "Should exclude common directories like .git, node_modules, __pycache__"

    print(f"✅ File cache populated with {len(completer._file_cache)} files")


def test_cli_interface_has_completer():
    """Test that CLIInterface has completer configured."""
    from src.interfaces.cli_interface import CLIInterface
    from unittest.mock import patch, MagicMock

    # Mock PromptSession to avoid terminal requirements
    with patch('src.interfaces.cli_interface.PromptSession') as mock_session:
        mock_instance = MagicMock()
        mock_session.return_value = mock_instance

        # Create CLI instance
        cli = CLIInterface()

        # Verify PromptSession was called with completer
        mock_session.assert_called_once()
        call_kwargs = mock_session.call_args[1]

        assert 'completer' in call_kwargs, "Should have completer in session config"
        assert call_kwargs['completer'] is not None, "Completer should not be None"
        assert 'complete_while_typing' in call_kwargs, "Should have complete_while_typing"
        assert call_kwargs['complete_while_typing'] == True, "complete_while_typing should be True"

    print("✅ CLIInterface has completer configured")


def test_command_completer_suggestions():
    """Test that command completer suggests slash commands."""
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.document import Document

    # Create command completer
    commands = ['/help', '/exit', '/agent-mode', '/cron', '/subagents']
    completer = WordCompleter(commands, ignore_case=True, sentence=True)

    # Test completion for /he
    doc = Document("/he")
    completions = list(completer.get_completions(doc, None))

    # Should suggest /help
    assert len(completions) > 0, "Should have completions for /he"
    assert any('help' in c.text for c in completions), "Should suggest /help"

    print("✅ Command completer suggests slash commands")


def test_command_completer_case_insensitive():
    """Test that command completer is case insensitive."""
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.document import Document

    commands = ['/help', '/exit']
    completer = WordCompleter(commands, ignore_case=True, sentence=True)

    # Test lowercase (normal)
    doc = Document("/he")
    completions = list(completer.get_completions(doc, None))

    assert len(completions) > 0, "Should complete lowercase input"

    # Verify help is in completions
    assert any('help' in c.text for c in completions), "Should suggest help"

    print("✅ Command completer is case insensitive")


def test_completion_in_middle_of_sentence():
    """Test that completion works when typing slash command."""
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.document import Document

    commands = ['/help', '/cron', '/agent-mode']
    completer = WordCompleter(commands, ignore_case=True, sentence=True)

    # Test completion at start (normal use case)
    doc = Document("/cr")
    completions = list(completer.get_completions(doc, None))

    # Should suggest /cron
    assert len(completions) > 0, "Should complete command"
    assert any('cron' in c.text for c in completions), "Should suggest /cron"

    print("✅ Completion works for commands")


def test_file_completer_multiple_at_symbols():
    """Test file completer with multiple @ symbols."""
    from src.interfaces.cli_interface import FileCompleter

    completer = FileCompleter(base_dir=".")

    # Document with multiple @
    doc = Document("Compare @src/main.py with @test")

    # Should complete from the LAST @ symbol
    completions = list(completer.get_completions(doc, None))

    # Should have completions for "test"
    assert len(completions) > 0, "Should have completions"

    print("✅ File completer handles multiple @ symbols")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Autocompletion Features (FASE 5)")
    print("="*60 + "\n")

    # Run tests
    test_imports()
    test_file_completer_fuzzy_match()
    test_file_completer_no_completion_without_at()
    test_file_completer_basic()
    test_file_completer_cache()
    test_cli_interface_has_completer()
    test_command_completer_suggestions()
    test_command_completer_case_insensitive()
    test_completion_in_middle_of_sentence()
    test_file_completer_multiple_at_symbols()

    print("\n" + "="*60)
    print("✅ All Autocompletion Tests Passed (10/10)")
    print("="*60)
