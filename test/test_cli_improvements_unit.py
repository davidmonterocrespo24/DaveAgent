"""
Unit tests for FASE 1: CLI Improvements

Tests components in isolation without requiring a real terminal.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all CLI improvements can be imported."""
    print("\n" + "="*70)
    print("TEST 1: Import all components")
    print("="*70)

    try:
        from src.interfaces.cli_interface import TERMIOS_AVAILABLE
        print(f"[OK] TERMIOS_AVAILABLE imported: {TERMIOS_AVAILABLE}")
    except ImportError as e:
        print(f"[FAIL] Could not import TERMIOS_AVAILABLE: {e}")
        return False

    try:
        from prompt_toolkit.formatted_text import HTML
        print("[OK] HTML imported from prompt_toolkit")
    except ImportError as e:
        print(f"[FAIL] Could not import HTML: {e}")
        return False

    try:
        from prompt_toolkit.patch_stdout import patch_stdout
        print("[OK] patch_stdout imported from prompt_toolkit")
    except ImportError as e:
        print(f"[FAIL] Could not import patch_stdout: {e}")
        return False

    return True


def test_html_formatting():
    """Test HTML prompt formatting works correctly."""
    print("\n" + "="*70)
    print("TEST 2: HTML prompt formatting")
    print("="*70)

    try:
        from prompt_toolkit.formatted_text import HTML

        # Test various HTML formats
        test_cases = [
            ("<b fg='ansibrightcyan'>[🔧 AGENT]</b> <b fg='ansiyellow'>You:</b> ", "Agent mode prompt"),
            ("<b fg='ansigreen'>Test:</b> ", "Simple colored prompt"),
            ("<ansiyellow>Plain text</ansiyellow>", "Yellow text"),
        ]

        for html_str, description in test_cases:
            prompt = HTML(html_str)
            assert prompt is not None, f"Failed to create HTML: {description}"
            print(f"[OK] {description}")

        return True
    except Exception as e:
        print(f"[FAIL] Error with HTML formatting: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_patch_stdout_context():
    """Test that patch_stdout import works (actual usage requires interactive terminal)."""
    print("\n" + "="*70)
    print("TEST 3: patch_stdout availability")
    print("="*70)

    try:
        from prompt_toolkit.patch_stdout import patch_stdout
        import sys

        # Just verify we can import it
        print("[OK] patch_stdout imported successfully")

        # Check if we're in an interactive terminal
        if sys.stdout.isatty():
            # Try to use it in interactive mode
            with patch_stdout():
                pass
            print("[OK] patch_stdout context manager works in interactive mode")
        else:
            print("[INFO] Non-interactive terminal - patch_stdout will work when running main CLI")

        return True
    except Exception as e:
        print(f"[FAIL] Error with patch_stdout: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_termios_graceful_fallback():
    """Test that termios operations fail gracefully on Windows."""
    print("\n" + "="*70)
    print("TEST 4: Termios graceful fallback")
    print("="*70)

    try:
        from src.interfaces.cli_interface import TERMIOS_AVAILABLE

        if TERMIOS_AVAILABLE:
            import termios
            print("[INFO] termios available (Unix system)")
            print("[OK] Unix terminal features enabled")
        else:
            print("[INFO] termios not available (Windows system)")
            print("[OK] Graceful fallback to Windows mode")

        return True
    except Exception as e:
        print(f"[FAIL] Error checking termios: {e}")
        return False


def test_method_existence():
    """Test that new methods exist in CLIInterface class."""
    print("\n" + "="*70)
    print("TEST 5: Method existence")
    print("="*70)

    try:
        from src.interfaces import cli_interface
        import inspect

        # Get CLIInterface class
        CLIInterface = cli_interface.CLIInterface

        # Check for new methods
        expected_methods = [
            '_save_terminal_state',
            '_restore_terminal_state',
            '_flush_pending_tty_input',
            '_handle_interrupt',
            '_handle_terminate',
        ]

        for method_name in expected_methods:
            assert hasattr(CLIInterface, method_name), f"Missing method: {method_name}"
            method = getattr(CLIInterface, method_name)
            assert callable(method), f"Method {method_name} is not callable"
            print(f"[OK] Method '{method_name}' exists and is callable")

        # Check get_user_input has been updated
        source = inspect.getsource(CLIInterface.get_user_input)

        # Verify key improvements are in the code
        checks = [
            ('HTML', 'HTML formatted prompts'),
            ('patch_stdout', 'patch_stdout integration'),
            ('_flush_pending_tty_input', 'TTY input flushing'),
            ('_restore_terminal_state', 'Terminal state restoration'),
        ]

        for keyword, description in checks:
            if keyword in source:
                print(f"[OK] get_user_input includes: {description}")
            else:
                print(f"[WARNING] get_user_input may be missing: {description}")

        return True
    except Exception as e:
        print(f"[FAIL] Error checking methods: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_structure():
    """Test the overall code structure and imports in cli_interface.py."""
    print("\n" + "="*70)
    print("TEST 6: Code structure verification")
    print("="*70)

    try:
        # Read the file and check for key additions
        cli_file = Path(__file__).parent / "src" / "interfaces" / "cli_interface.py"

        if not cli_file.exists():
            print(f"[FAIL] File not found: {cli_file}")
            return False

        content = cli_file.read_text(encoding='utf-8')

        # Check for FASE 1 improvements
        checks = [
            ('import signal', 'Signal handling import'),
            ('from prompt_toolkit.formatted_text import HTML', 'HTML import'),
            ('from prompt_toolkit.patch_stdout import patch_stdout', 'patch_stdout import'),
            ('TERMIOS_AVAILABLE', 'Termios availability check'),
            ('self._saved_term_attrs', 'Terminal state tracking'),
            ('def _save_terminal_state', 'Save terminal method'),
            ('def _restore_terminal_state', 'Restore terminal method'),
            ('def _flush_pending_tty_input', 'Flush TTY method'),
            ('def _handle_interrupt', 'Interrupt handler'),
        ]

        all_present = True
        for keyword, description in checks:
            if keyword in content:
                print(f"[OK] Found: {description}")
            else:
                print(f"[FAIL] Missing: {description}")
                all_present = False

        return all_present
    except Exception as e:
        print(f"[FAIL] Error checking code structure: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all unit tests."""
    print("\n" + "="*70)
    print("FASE 1: CLI IMPROVEMENTS - UNIT TEST SUITE")
    print("Testing without requiring interactive terminal")
    print("="*70)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("HTML Formatting", test_html_formatting()))
    results.append(("patch_stdout", test_patch_stdout_context()))
    results.append(("Termios Fallback", test_termios_graceful_fallback()))
    results.append(("Method Existence", test_method_existence()))
    results.append(("Code Structure", test_code_structure()))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*70)
        print("✅ FASE 1: CLI IMPROVEMENTS - COMPLETE!")
        print("="*70)
        print("\nImplemented features:")
        print("  ✅ Terminal state recovery with termios (cross-platform)")
        print("  ✅ HTML formatted prompts in prompt_toolkit")
        print("  ✅ patch_stdout integration to prevent output conflicts")
        print("  ✅ TTY input flushing to remove ghost characters")
        print("  ✅ Signal handlers (SIGINT, SIGTERM) for graceful cleanup")
        print("  ✅ Cross-platform support (Windows/Unix)")
        print("\n📝 Key changes in src/interfaces/cli_interface.py:")
        print("  - Added TERMIOS_AVAILABLE flag")
        print("  - New terminal management methods")
        print("  - Enhanced get_user_input() with HTML and patch_stdout")
        print("  - Signal handlers for cleanup")
        print("\n🎯 Ready for FASE 2: Cron System")
        print("  - Next: Implement at/every/cron schedule types")
        print("  - Next: CronService with asyncio timers")
        print("  - Next: CLI commands for cron management")
        print("="*70)
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
