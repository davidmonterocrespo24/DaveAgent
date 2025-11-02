"""
Herramientas web (Wikipedia, búsquedas, etc.)
"""
from src.tools.web.wikipedia_tools import (
    wiki_search, wiki_summary, wiki_content,
    wiki_page_info, wiki_random, wiki_set_language
)
from src.tools.web.web_search import (
    web_search, web_search_news
)

__all__ = [
    "wiki_search", "wiki_summary", "wiki_content",
    "wiki_page_info", "wiki_random", "wiki_set_language",
    "web_search", "web_search_news"
]
