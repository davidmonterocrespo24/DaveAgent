"""
Script de prueba para verificar todas las herramientas implementadas
"""
import asyncio
from tools import (
    read_file, write_file, list_dir, run_terminal_cmd,
    edit_file, file_search, grep_search, codebase_search,
    delete_file, diff_history
)


async def test_all_tools():
    """Prueba todas las herramientas"""
    print("="*60)
    print("PROBANDO TODAS LAS HERRAMIENTAS")
    print("="*60)
    print()

    # Test 1: write_file
    print("[TEST 1] write_file")
    result = await write_file("test_temp.txt", "Hello World!\nLine 2\nLine 3\n")
    print(f"  Result: {result[:80]}")
    print()

    # Test 2: read_file
    print("[TEST 2] read_file")
    result = await read_file("test_temp.txt", should_read_entire_file=True)
    print(f"  Result: {result[:80]}...")
    print()

    # Test 3: list_dir
    print("[TEST 3] list_dir")
    result = await list_dir(".")
    lines = result.split('\n')[:10]
    print(f"  Result (first 10 lines):\n    " + "\n    ".join(lines))
    print()

    # Test 4: edit_file
    print("[TEST 4] edit_file")
    result = await edit_file("test_temp.txt", 2, 2, "Modified Line 2\n")
    print(f"  Result: {result}")
    print()

    # Test 5: file_search
    print("[TEST 5] file_search")
    result = await file_search("test_temp")
    print(f"  Result: {result[:150]}...")
    print()

    # Test 6: grep_search
    print("[TEST 6] grep_search")
    result = await grep_search("async def", include_pattern="*.py", max_results=5)
    lines = result.split('\n')[:8]
    print(f"  Result (first 8 lines):\n    " + "\n    ".join(lines))
    print()

    # Test 7: codebase_search
    print("[TEST 7] codebase_search")
    result = await codebase_search("test_all_tools", max_results=3)
    print(f"  Result: {result[:200]}...")
    print()

    # Test 8: run_terminal_cmd (comando seguro, sin aprobación)
    print("[TEST 8] run_terminal_cmd (safe command)")
    result = await run_terminal_cmd("echo Hello from terminal", require_user_approval=False)
    print(f"  Result: SUCCESS" if "Comando ejecutado" in result or "Hello" in result else f"  Result: {result[:80]}")
    print()

    # Test 9: run_terminal_cmd (comando peligroso, requiere aprobación)
    print("[TEST 9] run_terminal_cmd (dangerous command - requires approval)")
    result = await run_terminal_cmd("pip install something", require_user_approval=True)
    print(f"  Result: APPROVAL REQUIRED" if "APPROVAL REQUIRED" in result or "ACTION REQUIRED" in result else "  Result: ERROR")
    print()

    # Test 10: diff_history
    print("[TEST 10] diff_history")
    result = await diff_history(max_commits=5)
    lines = result.split('\n')[:8]
    print(f"  Result (first 8 lines):\n    " + "\n    ".join(lines))
    print()

    # Test 11: delete_file
    print("[TEST 11] delete_file")
    result = await delete_file("test_temp.txt")
    print(f"  Result: {result}")
    print()

    print("="*60)
    print("TODAS LAS PRUEBAS COMPLETADAS")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_all_tools())
