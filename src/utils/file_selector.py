"""
Interactive File Selector - Allows selecting files with keyboard navigation
"""
import sys
import os
from typing import List, Optional
from .file_indexer import FileIndexer

# Try to import readchar for better cross-platform support
try:
    import readchar
    HAS_READCHAR = True
except ImportError:
    HAS_READCHAR = False

# ANSI escape codes for terminal control
class TerminalCodes:
    CLEAR_LINE = '\033[2K'
    MOVE_UP = '\033[A'
    MOVE_DOWN = '\033[B'
    CURSOR_START = '\r'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'


class FileSelector:
    """Interactive file selector with keyboard navigation"""

    def __init__(self, indexer: FileIndexer):
        """
        Initialize file selector

        Args:
            indexer: FileIndexer instance with indexed files
        """
        self.indexer = indexer
        self.max_display_items = 10  # Maximum files to show at once
        self.selected_index = 0
        self.scroll_offset = 0

    def _get_key(self) -> str:
        """
        Get a single keypress from user

        Returns:
            Key pressed
        """
        if HAS_READCHAR:
            key = readchar.readkey()
            if key == readchar.key.UP:
                return 'up'
            elif key == readchar.key.DOWN:
                return 'down'
            elif key == readchar.key.ENTER:
                return 'enter'
            elif key == readchar.key.ESC:
                return 'esc'
            elif key == readchar.key.BACKSPACE or key == '\x7f':
                return 'backspace'
            else:
                return key
        else:
            # Fallback for Windows without readchar
            if os.name == 'nt':
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\xe0':  # Arrow keys prefix on Windows
                        key = msvcrt.getch()
                        if key == b'H':
                            return 'up'
                        elif key == b'P':
                            return 'down'
                    elif key == b'\r':
                        return 'enter'
                    elif key == b'\x1b':
                        return 'esc'
                    elif key == b'\x08':
                        return 'backspace'
                    else:
                        return key.decode('utf-8', errors='ignore')
            else:
                # Unix-like systems
                import tty
                import termios
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    key = sys.stdin.read(1)
                    if key == '\x1b':  # ESC sequence
                        seq = sys.stdin.read(2)
                        if seq == '[A':
                            return 'up'
                        elif seq == '[B':
                            return 'down'
                        else:
                            return 'esc'
                    elif key == '\r' or key == '\n':
                        return 'enter'
                    elif key == '\x7f':
                        return 'backspace'
                    else:
                        return key
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ''

    def _render_file_list(
        self,
        files: List[str],
        query: str = "",
        show_header: bool = True
    ):
        """
        Render the file list to terminal

        Args:
            files: List of file paths to display
            query: Current search query
            show_header: Whether to show header
        """
        # Clear previous output
        if not show_header:
            # Move cursor up and clear lines
            for _ in range(self.max_display_items + 3):
                sys.stdout.write(TerminalCodes.MOVE_UP + TerminalCodes.CLEAR_LINE)
            sys.stdout.write(TerminalCodes.CURSOR_START)

        # Header
        if show_header:
            print(f"\n{TerminalCodes.BOLD}{TerminalCodes.CYAN}📁 Select a file (Arrow keys to navigate, Enter to select, Esc to cancel){TerminalCodes.RESET}")
            print(f"{TerminalCodes.DIM}Search: @{query}{TerminalCodes.RESET}")
            print(f"{TerminalCodes.DIM}─" * 60 + f"{TerminalCodes.RESET}")
        else:
            print(f"{TerminalCodes.BOLD}{TerminalCodes.CYAN}📁 Select a file (Arrow keys to navigate, Enter to select, Esc to cancel){TerminalCodes.RESET}")
            print(f"{TerminalCodes.DIM}Search: @{query}{TerminalCodes.RESET}")
            print(f"{TerminalCodes.DIM}─" * 60 + f"{TerminalCodes.RESET}")

        if not files:
            print(f"{TerminalCodes.YELLOW}No files found matching '{query}'{TerminalCodes.RESET}")
            for _ in range(self.max_display_items - 1):
                print()
            return

        # Calculate visible range
        total_files = len(files)
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.max_display_items, total_files)

        # Display files
        for i in range(start_idx, end_idx):
            file_path = files[i]
            is_selected = (i == self.selected_index)

            if is_selected:
                # Highlight selected item
                print(f"{TerminalCodes.GREEN}▶ {file_path}{TerminalCodes.RESET}")
            else:
                print(f"  {TerminalCodes.DIM}{file_path}{TerminalCodes.RESET}")

        # Fill remaining lines
        displayed_count = end_idx - start_idx
        for _ in range(self.max_display_items - displayed_count):
            print()

        # Footer with scroll indicator
        if total_files > self.max_display_items:
            scroll_pct = int((self.selected_index / (total_files - 1)) * 100) if total_files > 1 else 0
            print(f"{TerminalCodes.DIM}Showing {start_idx + 1}-{end_idx} of {total_files} files ({scroll_pct}%){TerminalCodes.RESET}")
        else:
            print(f"{TerminalCodes.DIM}Showing {total_files} file(s){TerminalCodes.RESET}")

        sys.stdout.flush()

    def select_file(self, initial_query: str = "") -> Optional[str]:
        """
        Show interactive file selector

        Args:
            initial_query: Initial search query

        Returns:
            Selected file path or None if cancelled
        """
        query = initial_query
        first_render = True

        while True:
            # Search files based on query
            matching_files = self.indexer.search_files(query)

            # Ensure selected index is valid
            if matching_files:
                self.selected_index = max(0, min(self.selected_index, len(matching_files) - 1))
                # Adjust scroll to keep selection visible
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
                elif self.selected_index >= self.scroll_offset + self.max_display_items:
                    self.scroll_offset = self.selected_index - self.max_display_items + 1
            else:
                self.selected_index = 0
                self.scroll_offset = 0

            # Render file list
            self._render_file_list(matching_files, query, show_header=first_render)
            first_render = False

            # Get user input
            key = self._get_key()

            if key == 'up':
                # Move selection up
                if self.selected_index > 0:
                    self.selected_index -= 1
            elif key == 'down':
                # Move selection down
                if matching_files and self.selected_index < len(matching_files) - 1:
                    self.selected_index += 1
            elif key == 'enter':
                # Select current file
                if matching_files and self.selected_index < len(matching_files):
                    selected_file = matching_files[self.selected_index]
                    # Clear the selector UI
                    for _ in range(self.max_display_items + 4):
                        sys.stdout.write(TerminalCodes.MOVE_UP + TerminalCodes.CLEAR_LINE)
                    sys.stdout.write(TerminalCodes.CURSOR_START)
                    sys.stdout.flush()
                    return selected_file
                return None
            elif key == 'esc':
                # Cancel selection
                # Clear the selector UI
                for _ in range(self.max_display_items + 4):
                    sys.stdout.write(TerminalCodes.MOVE_UP + TerminalCodes.CLEAR_LINE)
                sys.stdout.write(TerminalCodes.CURSOR_START)
                sys.stdout.flush()
                return None
            elif key == 'backspace':
                # Remove last character from query
                if query:
                    query = query[:-1]
                    self.selected_index = 0
                    self.scroll_offset = 0
            elif key and len(key) == 1 and key.isprintable():
                # Add character to query
                query += key
                self.selected_index = 0
                self.scroll_offset = 0


def select_file_interactive(root_dir: str = ".", initial_query: str = "") -> Optional[str]:
    """
    Convenience function to select a file interactively

    Args:
        root_dir: Root directory to index
        initial_query: Initial search query

    Returns:
        Selected file path or None if cancelled
    """
    indexer = FileIndexer(root_dir)
    indexer.index_directory()

    if indexer.get_file_count() == 0:
        print("No files found in directory")
        return None

    selector = FileSelector(indexer)
    return selector.select_file(initial_query)
