"""
Interactive File Selector - Clean file selection with scrollbar
"""
import os
import sys
from typing import List, Optional

from .file_indexer import FileIndexer

# Try to import readchar for better cross-platform support
try:
    import readchar

    HAS_READCHAR = True
except ImportError:
    HAS_READCHAR = False


class FileSelector:
    """Interactive file selector with visual scrollbar"""

    def __init__(self, indexer: FileIndexer):
        """
        Initialize file selector

        Args:
            indexer: FileIndexer instance with indexed files
        """
        self.indexer = indexer
        self.max_display_items = 15  # Files to show at once
        self.selected_index = 0
        self.scroll_offset = 0
        self.lines_drawn = 0  # Track how many lines we drew

    def _get_key(self) -> str:
        """Get a single keypress from user"""
        if HAS_READCHAR:
            try:
                key = readchar.readkey()
                if key == readchar.key.UP:
                    return 'up'
                elif key == readchar.key.DOWN:
                    return 'down'
                elif key == readchar.key.ENTER or key == '\r' or key == '\n':
                    return 'enter'
                elif key == readchar.key.ESC:
                    return 'esc'
                elif key == readchar.key.BACKSPACE or key == '\x7f' or key == '\x08':
                    return 'backspace'
                else:
                    return key
            except:
                return ''
        else:
            # Windows fallback
            if os.name == 'nt':
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\xe0':  # Arrow keys
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
                        try:
                            return key.decode('utf-8', errors='ignore')
                        except:
                            return ''
        return ''

    def _draw_scrollbar(self, position: int, total: int, height: int) -> str:
        """
        Create a visual scrollbar

        Args:
            position: Current position (0-based)
            total: Total number of items
            height: Height of scrollbar

        Returns:
            Scrollbar character
        """
        if total <= height:
            return '│'  # Full bar

        # Calculate scroll position
        scroll_pos = int((position / max(total - 1, 1)) * (height - 1))
        return '█' if scroll_pos == position % height else '│'

    def _move_cursor_up(self, lines: int):
        """Move cursor up by n lines"""
        if lines > 0:
            sys.stdout.write(f'\033[{lines}A')

    def _render_file_list(self, files: List[str], query: str):
        """
        Render the file list with scrollbar
        
        Args:
            files: List of file paths to display
            query: Current search query
        """
        # Move cursor up to overwrite previous render
        if self.lines_drawn > 0:
            self._move_cursor_up(self.lines_drawn)

        lines = []

        # Header
        lines.append("\033[1m\033[96m📁 File Selector\033[0m \033[2m(↑↓ navigate | Enter select | Esc cancel)\033[0m")
        lines.append(f"\033[2mSearch:\033[0m @{query}\033[K")  # Clear to end of line
        lines.append("\033[2m" + "─" * 70 + "\033[0m")

        if not files:
            lines.append("\033[93m⚠ No files found\033[0m\033[K")
            for _ in range(self.max_display_items - 1):
                lines.append("\033[K")  # Empty line with clear
        else:
            # Calculate visible range
            total_files = len(files)
            start_idx = self.scroll_offset
            end_idx = min(start_idx + self.max_display_items, total_files)

            # Display files with scrollbar
            for i in range(self.max_display_items):
                file_idx = start_idx + i

                # Scrollbar on the left
                if i < total_files - start_idx and file_idx < total_files:
                    # Calculate if scrollbar should show indicator here
                    scrollbar_height = self.max_display_items
                    indicator_pos = int((self.selected_index / max(total_files - 1, 1)) * (scrollbar_height - 1))

                    if i == indicator_pos:
                        scrollbar = "\033[96m█\033[0m"  # Indicator
                    else:
                        scrollbar = "\033[2m│\033[0m"  # Bar
                else:
                    scrollbar = " "

                # File display
                if file_idx < total_files:
                    file_path = files[file_idx]
                    is_selected = (file_idx == self.selected_index)

                    if is_selected:
                        # Highlighted selection
                        line = f"{scrollbar} \033[1m\033[92m▶ {file_path}\033[0m"
                    else:
                        # Normal file
                        line = f"{scrollbar}   \033[2m{file_path}\033[0m"

                    lines.append(line + "\033[K")  # Clear rest of line
                else:
                    # Empty line
                    lines.append(scrollbar + "\033[K")

        # Footer with position info
        if files:
            total = len(files)
            current = self.selected_index + 1
            lines.append("\033[2m" + "─" * 70 + "\033[0m")
            lines.append(f"\033[2mFile {current}/{total} | Showing {start_idx + 1}-{min(end_idx, total)}\033[0m\033[K")
        else:
            lines.append("\033[2m" + "─" * 70 + "\033[0m")
            lines.append("\033[2mNo files to display\033[0m\033[K")

        # Clear any remaining lines from previous render if new render is shorter
        # (Though in this fixed height implementation, it shouldn't vary much)
        lines.append("\033[J")

        # Write all lines at once to reduce flickering
        output = '\n'.join(lines)
        sys.stdout.write(output)  # No extra newline at end to avoid scrolling issues
        sys.stdout.flush()

        # Track lines for clearing (number of \n in output + 1 for the last line)
        # We count the actual lines we printed
        self.lines_drawn = len(
            lines) - 1  # -1 because the last \033[J is not a new line visually but part of the last line logic
        # Actually, let's be precise: we printed len(lines) lines separated by \n.
        # So the cursor is now at the end of the last line.
        # If we want to move back up to the start, we need to move up len(lines) - 1 times?
        # No, if we print "A\nB", we are on line B. To go to A, we move up 1.
        # So we need to move up len(lines) - 1.
        self.lines_drawn = len(lines) - 1

    def select_file(self, initial_query: str = "") -> Optional[str]:
        """
        Show interactive file selector

        Args:
            initial_query: Initial search query

        Returns:
            Selected file path or None if cancelled
        """
        query = initial_query
        self.lines_drawn = 0

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
            self._render_file_list(matching_files, query)

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
                    self._clear_screen()
                    return selected_file
                return None
            elif key == 'esc':
                # Cancel selection
                self._clear_screen()
                return None
            elif key == 'backspace':
                # Remove last character from query
                if query:
                    query = query[:-1]
                    self.selected_index = 0
                    self.scroll_offset = 0
            elif key and len(key) == 1 and key.isprintable() and key != ' ':
                # Add character to query (except space)
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

    # Show indexing message
    print("\033[2m📁 Indexing files...\033[0m", end='', flush=True)
    indexer.index_directory()

    # Clear indexing message
    sys.stdout.write('\r\033[2K')
    sys.stdout.flush()

    if indexer.get_file_count() == 0:
        print("\033[93m⚠ No files found in directory\033[0m")
        return None

    selector = FileSelector(indexer)
    return selector.select_file(initial_query)
