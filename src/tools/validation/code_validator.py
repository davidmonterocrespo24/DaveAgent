"""
Code Validation Tools - Verify syntax and detect errors after editing files
Provides language-specific validators to ensure code integrity
"""
import ast
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import os


# Workspace base path
WORKSPACE = Path(os.getcwd()).resolve()


async def validate_python_syntax(filepath: str, show_details: bool = True) -> str:
    """
    Validate Python file syntax using ast.parse().
    Detects syntax errors, indentation issues, and invalid Python code.

    Args:
        filepath: Path to the Python file to validate
        show_details: If True, shows detailed error information with line numbers

    Returns:
        str: Validation result with success message or detailed error information

    Examples:
        >>> await validate_python_syntax("main.py")
        >>> await validate_python_syntax("src/utils/helper.py", show_details=True)
    """
    try:
        # Resolve path
        target = WORKSPACE / filepath if not Path(filepath).is_absolute() else Path(filepath)

        if not target.exists():
            return f"❌ ERROR: File '{filepath}' not found"

        if not str(target).endswith('.py'):
            return f"⚠️  WARNING: File '{filepath}' is not a Python file (.py)"

        # Read file content
        with open(target, 'r', encoding='utf-8') as f:
            code = f.read()

        # Attempt to parse with AST
        try:
            ast.parse(code, filename=str(target))

            # Success - no syntax errors
            lines = code.count('\n') + 1
            return (
                f"✅ Python syntax validation PASSED\n"
                f"   File: {filepath}\n"
                f"   Lines: {lines}\n"
                f"   Status: No syntax errors detected"
            )

        except SyntaxError as e:
            # Syntax error detected
            error_msg = f"❌ Python syntax validation FAILED\n"
            error_msg += f"   File: {filepath}\n"
            error_msg += f"   Error: {e.msg}\n"
            error_msg += f"   Line {e.lineno}: {e.text.strip() if e.text else '(empty line)'}\n"

            if show_details and e.lineno:
                # Show context around the error
                lines = code.split('\n')
                start = max(0, e.lineno - 3)
                end = min(len(lines), e.lineno + 2)

                error_msg += f"\n   Context:\n"
                for i in range(start, end):
                    line_num = i + 1
                    prefix = ">>>" if line_num == e.lineno else "   "
                    error_msg += f"   {prefix} {line_num:4d} | {lines[i]}\n"

                if e.offset:
                    error_msg += f"   {'':>8} | {' ' * (e.offset - 1)}^\n"

            return error_msg

    except FileNotFoundError:
        return f"❌ ERROR: File '{filepath}' not found"
    except UnicodeDecodeError:
        return f"❌ ERROR: Cannot read '{filepath}' - invalid UTF-8 encoding"
    except Exception as e:
        return f"❌ ERROR validating Python file: {str(e)}"


async def validate_javascript_syntax(filepath: str, use_node: bool = True) -> str:
    """
    Validate JavaScript file syntax.

    Args:
        filepath: Path to the JavaScript file to validate
        use_node: If True, uses 'node --check' command (requires Node.js)
                  If False, performs basic syntax checks only

    Returns:
        str: Validation result with success message or error details
    """
    try:
        target = WORKSPACE / filepath if not Path(filepath).is_absolute() else Path(filepath)

        if not target.exists():
            return f"❌ ERROR: File '{filepath}' not found"

        if not str(target).endswith(('.js', '.jsx')):
            return f"⚠️  WARNING: File '{filepath}' is not a JavaScript file (.js, .jsx)"

        if use_node:
            # Try using Node.js --check flag
            try:
                result = subprocess.run(
                    ['node', '--check', str(target)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    with open(target, 'r', encoding='utf-8') as f:
                        lines = f.read().count('\n') + 1
                    return (
                        f"✅ JavaScript syntax validation PASSED\n"
                        f"   File: {filepath}\n"
                        f"   Lines: {lines}\n"
                        f"   Status: No syntax errors detected (validated with Node.js)"
                    )
                else:
                    return (
                        f"❌ JavaScript syntax validation FAILED\n"
                        f"   File: {filepath}\n"
                        f"   Error: {result.stderr.strip()}"
                    )

            except FileNotFoundError:
                # Node.js not installed, fall back to basic validation
                return await _basic_javascript_validation(target, filepath)
            except subprocess.TimeoutExpired:
                return f"❌ ERROR: Validation timeout for '{filepath}'"
        else:
            return await _basic_javascript_validation(target, filepath)

    except Exception as e:
        return f"❌ ERROR validating JavaScript file: {str(e)}"


async def _basic_javascript_validation(target: Path, filepath: str) -> str:
    """Basic JavaScript syntax validation without Node.js"""
    try:
        with open(target, 'r', encoding='utf-8') as f:
            code = f.read()

        # Basic checks
        lines = code.count('\n') + 1

        # Check for common syntax errors
        issues = []

        # Unbalanced braces
        if code.count('{') != code.count('}'):
            issues.append("Unbalanced braces {} detected")

        # Unbalanced brackets
        if code.count('[') != code.count(']'):
            issues.append("Unbalanced brackets [] detected")

        # Unbalanced parentheses
        if code.count('(') != code.count(')'):
            issues.append("Unbalanced parentheses () detected")

        if issues:
            return (
                f"⚠️  JavaScript basic validation WARNING\n"
                f"   File: {filepath}\n"
                f"   Lines: {lines}\n"
                f"   Issues found:\n" +
                '\n'.join(f"   - {issue}" for issue in issues) +
                f"\n\n   Note: Install Node.js for accurate syntax validation"
            )

        return (
            f"✅ JavaScript basic validation PASSED\n"
            f"   File: {filepath}\n"
            f"   Lines: {lines}\n"
            f"   Status: No obvious syntax errors (basic check only)\n"
            f"   Note: Install Node.js for accurate validation"
        )

    except Exception as e:
        return f"❌ ERROR in basic validation: {str(e)}"


async def validate_typescript_syntax(filepath: str) -> str:
    """
    Validate TypeScript file syntax using tsc compiler.

    Args:
        filepath: Path to the TypeScript file to validate

    Returns:
        str: Validation result with success message or error details
    """
    try:
        target = WORKSPACE / filepath if not Path(filepath).is_absolute() else Path(filepath)

        if not target.exists():
            return f"❌ ERROR: File '{filepath}' not found"

        if not str(target).endswith(('.ts', '.tsx')):
            return f"⚠️  WARNING: File '{filepath}' is not a TypeScript file (.ts, .tsx)"

        # Try using TypeScript compiler
        try:
            result = subprocess.run(
                ['tsc', '--noEmit', '--skipLibCheck', str(target)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                with open(target, 'r', encoding='utf-8') as f:
                    lines = f.read().count('\n') + 1
                return (
                    f"✅ TypeScript syntax validation PASSED\n"
                    f"   File: {filepath}\n"
                    f"   Lines: {lines}\n"
                    f"   Status: No syntax errors detected"
                )
            else:
                return (
                    f"❌ TypeScript syntax validation FAILED\n"
                    f"   File: {filepath}\n"
                    f"   Errors:\n{result.stdout}"
                )

        except FileNotFoundError:
            return (
                f"⚠️  TypeScript compiler not found\n"
                f"   File: {filepath}\n"
                f"   Install TypeScript with: npm install -g typescript"
            )
        except subprocess.TimeoutExpired:
            return f"❌ ERROR: Validation timeout for '{filepath}'"

    except Exception as e:
        return f"❌ ERROR validating TypeScript file: {str(e)}"


async def validate_json_file(filepath: str) -> str:
    """
    Validate JSON file syntax.

    Args:
        filepath: Path to the JSON file to validate

    Returns:
        str: Validation result with success message or error details
    """
    try:
        target = WORKSPACE / filepath if not Path(filepath).is_absolute() else Path(filepath)

        if not target.exists():
            return f"❌ ERROR: File '{filepath}' not found"

        with open(target, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            data = json.loads(content)

            # Count elements
            if isinstance(data, dict):
                element_count = f"{len(data)} keys"
            elif isinstance(data, list):
                element_count = f"{len(data)} items"
            else:
                element_count = "1 value"

            return (
                f"✅ JSON validation PASSED\n"
                f"   File: {filepath}\n"
                f"   Type: {type(data).__name__}\n"
                f"   Elements: {element_count}\n"
                f"   Status: Valid JSON format"
            )

        except json.JSONDecodeError as e:
            return (
                f"❌ JSON validation FAILED\n"
                f"   File: {filepath}\n"
                f"   Error: {e.msg}\n"
                f"   Line {e.lineno}, Column {e.colno}"
            )

    except FileNotFoundError:
        return f"❌ ERROR: File '{filepath}' not found"
    except UnicodeDecodeError:
        return f"❌ ERROR: Cannot read '{filepath}' - invalid UTF-8 encoding"
    except Exception as e:
        return f"❌ ERROR validating JSON file: {str(e)}"


async def validate_file_after_edit(filepath: str) -> str:
    """
    Automatically detect file type and run appropriate validation.

    This is a convenience function that routes to the correct validator
    based on file extension.

    Args:
        filepath: Path to the file to validate

    Returns:
        str: Validation result from the appropriate validator
    """
    try:
        # Determine file extension
        ext = Path(filepath).suffix.lower()

        # Route to appropriate validator
        if ext == '.py':
            return await validate_python_syntax(filepath)
        elif ext in ('.js', '.jsx'):
            return await validate_javascript_syntax(filepath)
        elif ext in ('.ts', '.tsx'):
            return await validate_typescript_syntax(filepath)
        elif ext == '.json':
            return await validate_json_file(filepath)
        else:
            # Generic validation for other file types
            return await validate_generic_file(filepath)

    except Exception as e:
        return f"❌ ERROR in auto-validation: {str(e)}"


async def validate_generic_file(filepath: str) -> str:
    """
    Generic file validation for unsupported languages.
    Checks if file exists, is readable, and has valid UTF-8 encoding.

    Args:
        filepath: Path to the file to validate

    Returns:
        str: Basic validation result
    """
    try:
        target = WORKSPACE / filepath if not Path(filepath).is_absolute() else Path(filepath)

        if not target.exists():
            return f"❌ ERROR: File '{filepath}' not found"

        # Try to read the file
        with open(target, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.count('\n') + 1
        size = len(content)
        ext = target.suffix or "no extension"

        return (
            f"✅ Generic file validation PASSED\n"
            f"   File: {filepath}\n"
            f"   Type: {ext}\n"
            f"   Lines: {lines}\n"
            f"   Size: {size} bytes\n"
            f"   Status: File is readable and has valid UTF-8 encoding\n"
            f"   Note: Language-specific syntax validation not available for this file type"
        )

    except FileNotFoundError:
        return f"❌ ERROR: File '{filepath}' not found"
    except UnicodeDecodeError:
        return (
            f"⚠️  WARNING: File '{filepath}' has encoding issues\n"
            f"   The file may be binary or use non-UTF-8 encoding"
        )
    except Exception as e:
        return f"❌ ERROR validating file: {str(e)}"
