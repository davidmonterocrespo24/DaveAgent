"""
Web Search Tool - Búsqueda web en tiempo real usando DuckDuckGo
"""
import logging
from typing import Dict, List


async def web_search(query: str, max_results: int = 5) -> str:
    """
    Busca información en tiempo real en la web usando DuckDuckGo.

    Esta herramienta permite buscar información actualizada que no está
    en los datos de entrenamiento del modelo.

    Args:
        query: Consulta de búsqueda
        max_results: Número máximo de resultados (default: 5)

    Returns:
        str: Resultados de búsqueda formateados con títulos, snippets y URLs

    Examples:
        >>> await web_search("Python 3.12 new features")
        >>> await web_search("AutoGen 0.4 documentation", max_results=3)
    """
    try:
        # Intentar importar duckduckgo_search
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return (
                "ERROR: duckduckgo_search no está instalado.\n"
                "Instalar con: pip install duckduckgo-search"
            )

        # Realizar búsqueda
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
        except Exception as search_error:
            logging.error(f"Error en búsqueda DuckDuckGo: {search_error}")
            return f"ERROR al buscar '{query}': {str(search_error)}"

        if not results:
            return f"No se encontraron resultados para '{query}'"

        # Formatear resultados
        output = f"🔍 Resultados de búsqueda para: '{query}'\n"
        output += f"{'=' * 70}\n\n"

        for i, result in enumerate(results, 1):
            title = result.get('title', 'Sin título')
            snippet = result.get('body', 'Sin descripción')
            url = result.get('href', '')

            output += f"{i}. **{title}**\n"
            output += f"   {snippet}\n"
            output += f"   🔗 {url}\n\n"

        return output

    except Exception as e:
        error_msg = f"Error en web_search: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def web_search_news(query: str, max_results: int = 5) -> str:
    """
    Busca noticias recientes en la web.

    Args:
        query: Consulta de búsqueda de noticias
        max_results: Número máximo de resultados (default: 5)

    Returns:
        str: Resultados de noticias formateados
    """
    try:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return (
                "ERROR: duckduckgo_search no está instalado.\n"
                "Instalar con: pip install duckduckgo-search"
            )

        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=max_results))
        except Exception as search_error:
            logging.error(f"Error en búsqueda de noticias: {search_error}")
            return f"ERROR al buscar noticias '{query}': {str(search_error)}"

        if not results:
            return f"No se encontraron noticias para '{query}'"

        # Formatear resultados
        output = f"📰 Noticias sobre: '{query}'\n"
        output += f"{'=' * 70}\n\n"

        for i, result in enumerate(results, 1):
            title = result.get('title', 'Sin título')
            snippet = result.get('body', 'Sin descripción')
            url = result.get('url', '')
            date = result.get('date', 'Fecha desconocida')
            source = result.get('source', 'Fuente desconocida')

            output += f"{i}. **{title}**\n"
            output += f"   {snippet}\n"
            output += f"   📅 {date} | 📰 {source}\n"
            output += f"   🔗 {url}\n\n"

        return output

    except Exception as e:
        error_msg = f"Error en web_search_news: {str(e)}"
        logging.error(error_msg)
        return error_msg
