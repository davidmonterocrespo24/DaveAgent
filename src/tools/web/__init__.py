"""
Herramientas web (Wikipedia, búsquedas, etc.)
"""
from src.tools.web.wikipedia_tools import (
    wiki_search, wiki_summary, wiki_content,
    wiki_page_info, wiki_random, wiki_set_language
)

__all__ = [
    "wiki_search", "wiki_summary", "wiki_content",
    "wiki_page_info", "wiki_random", "wiki_set_language"
]
