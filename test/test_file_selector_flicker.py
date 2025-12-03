import sys
import os
from unittest.mock import MagicMock, patch
from src.utils.file_selector import FileSelector, FileIndexer

def test_file_selector_rendering():
    # Mock FileIndexer
    indexer = MagicMock(spec=FileIndexer)
    indexer.search_files.return_value = ["file1.txt", "file2.py", "file3.md"]
    
    selector = FileSelector(indexer)
    
    # Capture stdout
    with patch('sys.stdout') as mock_stdout:
        # First render
        selector._render_file_list(["file1.txt"], "")
        
        # Check that we didn't move cursor up on first render
        # We expect write calls. Let's inspect the calls.
        writes = [call.args[0] for call in mock_stdout.write.call_args_list]
        full_output = "".join(writes)
        
        if "\033[A" in full_output:
            sys.stderr.write("FAIL: Found cursor up movement on first render\n")
        else:
            sys.stderr.write("PASS: No cursor up movement on first render\n")
            
        # Second render (simulate update)
        selector._render_file_list(["file1.txt"], "f")
        
        writes = [call.args[0] for call in mock_stdout.write.call_args_list]
        # The second render should start with cursor movement
        # We need to check the calls made AFTER the first render.
        # Since mock accumulates, we can check the last few calls or reset mock.
        
    with patch('sys.stdout') as mock_stdout:
        # Reset lines_drawn to simulate state after first render
        selector.lines_drawn = 10 
        
        selector._render_file_list(["file1.txt"], "f")
        
        writes = [call.args[0] for call in mock_stdout.write.call_args_list]
        full_output = "".join(writes)
        
        # Check for cursor up sequence
        if "\033[10A" in full_output:
            sys.stderr.write("PASS: Found correct cursor up sequence \\033[10A\n")
        else:
            sys.stderr.write(f"FAIL: Did not find cursor up sequence \\033[10A. Output start: {full_output[:20]!r}\n")

        # Check for clear line sequences
        if "\033[K" in full_output:
            sys.stderr.write("PASS: Found clear line sequence \\033[K\n")
        else:
            sys.stderr.write("FAIL: Did not find clear line sequence \\033[K\n")
            
        # Check for clear end of screen sequence
        if "\033[J" in full_output:
            sys.stderr.write("PASS: Found clear end of screen sequence \\033[J\n")
        else:
            sys.stderr.write("FAIL: Did not find clear end of screen sequence \\033[J\n")

if __name__ == "__main__":
    try:
        test_file_selector_rendering()
        print("Test execution completed.")
    except Exception as e:
        print(f"Test failed with exception: {e}")
