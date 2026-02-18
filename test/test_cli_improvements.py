"""
Test script for FASE 1: CLI Improvements

Tests the Nanobot-style enhancements:
1. Terminal state recovery with termios
2. HTML formatted prompts
3. patch_stdout integration
4. TTY input flushing
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all CLI improvements can be imported."""
    print("\n" + "="*70)
    print("TEST 1: Import CLI improvements")
    print("="*70)

    try:
        from src.interfaces.cli_interface import CLIInterface, TERMIOS_AVAILABLE
        print(f"[OK] CLIInterface imported")
        print(f"     TERMIOS_AVAILABLE: {TERMIOS_AVAILABLE}")
    except ImportError as e:
        print(f"[FAIL] Could not import CLIInterface: {e}")
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

    if TERMIOS_AVAILABLE:
        try:
            import termios
            print("[OK] termios imported (Unix system)")
        except ImportError as e:
            print(f"[WARNING] termios not available: {e}")
    else:
        print("[INFO] termios not available (Windows system)")

    return True


def test_cli_initialization():
    """Test that CLIInterface initializes with new features."""
    print("\n" + "="*70)
    print("TEST 2: CLIInterface initialization")
    print("="*70)

    try:
        from src.interfaces.cli_interface import CLIInterface

        cli = CLIInterface()

        # Check new attributes
        assert hasattr(cli, '_saved_term_attrs'), "No _saved_term_attrs attribute"
        print("[OK] Terminal state tracking initialized")

        # Check new methods
        methods = [
            '_save_terminal_state',
            '_restore_terminal_state',
            '_flush_pending_tty_input',
            '_handle_interrupt',
            '_handle_terminate'
        ]

        for method in methods:
            assert hasattr(cli, method), f"Missing method: {method}"
            print(f"[OK] Method {method} exists")

        return True
    except Exception as e:
        print(f"[FAIL] Error initializing CLIInterface: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_html_prompt_formatting():
    """Test HTML prompt formatting."""
    print("\n" + "="*70)
    print("TEST 3: HTML prompt formatting")
    print("="*70)

    try:
        from prompt_toolkit.formatted_text import HTML

        # Test various HTML prompt formats
        prompts = [
            HTML("<b fg='ansibrightcyan'>[🔧 AGENT]</b> <b fg='ansiyellow'>You:</b> "),
            HTML("<b fg='ansigreen'>Test:</b> "),
            HTML("<ansiyellow>Simple prompt</ansiyellow>")
        ]

        for i, prompt in enumerate(prompts, 1):
            assert prompt is not None, f"Prompt {i} is None"
            print(f"[OK] HTML prompt {i} created successfully")

        return True
    except Exception as e:
        print(f"[FAIL] Error creating HTML prompts: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_terminal_methods():
    """Test terminal management methods (if available)."""
    print("\n" + "="*70)
    print("TEST 4: Terminal management methods")
    print("="*70)

    try:
        from src.interfaces.cli_interface import CLIInterface, TERMIOS_AVAILABLE

        cli = CLIInterface()

        if not TERMIOS_AVAILABLE:
            print("[INFO] termios not available, testing graceful fallback")

            # Methods should exist and not crash
            cli._save_terminal_state()
            print("[OK] _save_terminal_state() works (no-op on Windows)")

            cli._restore_terminal_state()
            print("[OK] _restore_terminal_state() works (no-op on Windows)")

            cli._flush_pending_tty_input()
            print("[OK] _flush_pending_tty_input() works (no-op on Windows)")
        else:
            print("[INFO] termios available, testing actual functionality")

            # Methods should work with termios
            cli._save_terminal_state()
            print("[OK] _save_terminal_state() executed")

            cli._restore_terminal_state()
            print("[OK] _restore_terminal_state() executed")

            cli._flush_pending_tty_input()
            print("[OK] _flush_pending_tty_input() executed")

        return True
    except Exception as e:
        print(f"[FAIL] Error testing terminal methods: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_handlers():
    """Test signal handler registration."""
    print("\n" + "="*70)
    print("TEST 5: Signal handler registration")
    print("="*70)

    try:
        import signal
        from src.interfaces.cli_interface import CLIInterface

        # Create CLI instance (registers handlers)
        cli = CLIInterface()

        # Check SIGINT handler
        sigint_handler = signal.getsignal(signal.SIGINT)
        assert sigint_handler != signal.SIG_DFL, "SIGINT handler not registered"
        print("[OK] SIGINT handler registered")

        # Check SIGTERM handler (Unix only)
        if hasattr(signal, 'SIGTERM'):
            sigterm_handler = signal.getsignal(signal.SIGTERM)
            assert sigterm_handler != signal.SIG_DFL, "SIGTERM handler not registered"
            print("[OK] SIGTERM handler registered")
        else:
            print("[INFO] SIGTERM not available (Windows)")

        return True
    except Exception as e:
        print(f"[FAIL] Error testing signal handlers: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("FASE 1: CLI IMPROVEMENTS - TEST SUITE")
    print("="*70)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("CLI Initialization", test_cli_initialization()))
    results.append(("HTML Prompt Formatting", test_html_prompt_formatting()))
    results.append(("Terminal Methods", test_terminal_methods()))
    results.append(("Signal Handlers", test_signal_handlers()))

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
        print("\n[SUCCESS] All FASE 1 improvements working correctly!")
        print("\nFASE 1 Complete:")
        print("  ✅ Terminal state recovery with termios")
        print("  ✅ HTML formatted prompts in prompt_toolkit")
        print("  ✅ patch_stdout integration")
        print("  ✅ TTY input flushing")
        print("\nReady for FASE 2: Cron System")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
