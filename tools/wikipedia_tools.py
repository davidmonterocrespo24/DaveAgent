"""
Herramientas de Wikipedia para AutoGen - Búsqueda y acceso a contenido de Wikipedia
"""
import logging
from importlib import util


def _check_wikipedia():
    """Verifica si wikipedia está instalado"""
    if util.find_spec("wikipedia") is None:
        raise ImportError("wikipedia package no disponible. Instalar con: pip install wikipedia")
    import wikipedia
    wikipedia.set_lang("es")  # Configurar idioma por defecto
    return wikipedia


async def wiki_search(query: str, max_results: int = 10) -> str:
    """
    Busca en Wikipedia y retorna títulos de páginas relacionadas.

    Args:
        query: Consulta de búsqueda
        max_results: Número máximo de resultados (default: 10)

    Returns:
        str: Lista de títulos encontrados o mensaje de error
    """
    try:
        wikipedia = _check_wikipedia()
        search_results = wikipedia.search(query, results=max_results, suggestion=True)

        if isinstance(search_results, tuple):
            results, suggestion = search_results
            output = f"Resultados de búsqueda para '{query}':\n\n"
            for i, title in enumerate(results, 1):
                output += f"{i}. {title}\n"
            if suggestion:
                output += f"\n¿Quisiste decir?: {suggestion}"
            return output
        else:
            output = f"Resultados de búsqueda para '{query}':\n\n"
            for i, title in enumerate(search_results, 1):
                output += f"{i}. {title}\n"
            return output

    except Exception as e:
        error_msg = f"Error buscando en Wikipedia '{query}': {str(e)}"
        logging.error(error_msg)
        return error_msg


async def wiki_summary(title: str, sentences: int = 5) -> str:
    """
    Obtiene un resumen de una página de Wikipedia.

    Args:
        title: Título de la página de Wikipedia
        sentences: Número de oraciones del resumen (default: 5)

    Returns:
        str: Resumen de la página o mensaje de error
    """
    try:
        wikipedia = _check_wikipedia()
        summary = wikipedia.summary(title, sentences=sentences, auto_suggest=True)
        return f"=== {title} ===\n\n{summary}"

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:10]  # Limitar a 10 opciones
        output = f"'{title}' es una página de desambiguación. Opciones:\n\n"
        for i, option in enumerate(options, 1):
            output += f"{i}. {option}\n"
        return output

    except wikipedia.exceptions.PageError:
        return f"ERROR: No se encontró la página '{title}' en Wikipedia"

    except Exception as e:
        error_msg = f"Error obteniendo resumen de '{title}': {str(e)}"
        logging.error(error_msg)
        return error_msg


async def wiki_content(title: str, max_chars: int = 5000) -> str:
    """
    Obtiene el contenido completo de una página de Wikipedia.

    Args:
        title: Título de la página de Wikipedia
        max_chars: Máximo de caracteres a retornar (default: 5000)

    Returns:
        str: Contenido de la página o mensaje de error
    """
    try:
        wikipedia = _check_wikipedia()
        page = wikipedia.page(title, auto_suggest=True)

        content = f"=== {page.title} ===\n"
        content += f"URL: {page.url}\n\n"
        content += page.content

        # Limitar caracteres si es necesario
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n... (contenido truncado)"

        return content

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:10]
        output = f"'{title}' es una página de desambiguación. Opciones:\n\n"
        for i, option in enumerate(options, 1):
            output += f"{i}. {option}\n"
        return output

    except wikipedia.exceptions.PageError:
        return f"ERROR: No se encontró la página '{title}' en Wikipedia"

    except Exception as e:
        error_msg = f"Error obteniendo contenido de '{title}': {str(e)}"
        logging.error(error_msg)
        return error_msg


async def wiki_page_info(title: str) -> str:
    """
    Obtiene información detallada sobre una página de Wikipedia.

    Args:
        title: Título de la página de Wikipedia

    Returns:
        str: Información detallada de la página
    """
    try:
        wikipedia = _check_wikipedia()
        page = wikipedia.page(title, auto_suggest=True)

        output = f"=== Información de: {page.title} ===\n\n"
        output += f"URL: {page.url}\n"
        output += f"Resumen: {page.summary[:300]}...\n\n"
        output += f"Categorías ({len(page.categories)}):\n"
        for cat in page.categories[:10]:
            output += f"  - {cat}\n"

        output += f"\nEnlaces relacionados ({len(page.links)}):\n"
        for link in page.links[:10]:
            output += f"  - {link}\n"

        output += f"\nReferencias: {len(page.references)} enlaces\n"
        output += f"Imágenes: {len(page.images)} imágenes\n"

        return output

    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:10]
        output = f"'{title}' es una página de desambiguación. Opciones:\n\n"
        for i, option in enumerate(options, 1):
            output += f"{i}. {option}\n"
        return output

    except wikipedia.exceptions.PageError:
        return f"ERROR: No se encontró la página '{title}' en Wikipedia"

    except Exception as e:
        error_msg = f"Error obteniendo información de '{title}': {str(e)}"
        logging.error(error_msg)
        return error_msg


async def wiki_random(count: int = 1) -> str:
    """
    Obtiene títulos de páginas aleatorias de Wikipedia.

    Args:
        count: Número de páginas aleatorias (default: 1)

    Returns:
        str: Títulos de páginas aleatorias
    """
    try:
        wikipedia = _check_wikipedia()

        if count == 1:
            random_title = wikipedia.random()
            return f"Página aleatoria: {random_title}"
        else:
            random_titles = wikipedia.random(count)
            output = f"Páginas aleatorias ({count}):\n\n"
            for i, title in enumerate(random_titles, 1):
                output += f"{i}. {title}\n"
            return output

    except Exception as e:
        error_msg = f"Error obteniendo páginas aleatorias: {str(e)}"
        logging.error(error_msg)
        return error_msg


async def wiki_set_language(language: str) -> str:
    """
    Cambia el idioma de Wikipedia.

    Args:
        language: Código de idioma (ej: 'en', 'es', 'fr')

    Returns:
        str: Mensaje de confirmación o error
    """
    try:
        wikipedia = _check_wikipedia()
        wikipedia.set_lang(language)
        return f"✓ Idioma de Wikipedia cambiado a: {language}"

    except Exception as e:
        error_msg = f"Error cambiando idioma a '{language}': {str(e)}"
        logging.error(error_msg)
        return error_msg
