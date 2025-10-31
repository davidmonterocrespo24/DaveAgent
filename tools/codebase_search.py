import concurrent.futures as cf
import re
from pathlib import Path
from typing import List, Optional, Sequence

# Importa el decorador de herramientas desde el ADK de watsonx Orchestrate
from ibm_watsonx_orchestrate.agent_builder.tools import tool

# --------------------------------------------------------------------------- #
# Configuración interna
# --------------------------------------------------------------------------- #
DEFAULT_EXTS: Sequence[str] = (".py", ".js", ".ts", ".java",
                               ".cpp", ".c", ".h")          # extensiones a inspeccionar
MAX_RESULTS: int = 50                                       # tope de paths devueltos
CASE_SENSITIVE: bool = False                                # búsqueda case-insensitive


# --------------------------------------------------------------------------- #
# Implementación auxiliar
# --------------------------------------------------------------------------- #
def _iter_code_files(roots: Sequence[Path], exts: Sequence[str]) -> list[Path]:
    """Recorre recursivamente los directorios dados devolviendo paths con extensiones deseadas."""
    paths: list[Path] = []
    for root in roots:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                paths.append(p)
    return paths


def _file_contains(pattern: re.Pattern[str], path: Path) -> Optional[Path]:
    """Devuelve el propio path si contiene la coincidencia; None en caso contrario/exception."""
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            if any(pattern.search(line) for line in f):
                return path
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------- #
# Firma requerida por el agente                                                 
# --------------------------------------------------------------------------- #
@tool
def codebase_search(
    query: str,
    target_directories: Optional[List[str]] = None,
    explanation: str = "",
) -> str:
    """
    Find snippets of code from the codebase most relevant to the search query.
    This is a semantic search tool, so the query should ask for something semantically
    matching what is needed.

    Parameters
    ----------
    query : str
        Search query (should be reused verbatim from user's prompt).
    target_directories : list[str] | None
        Optional list of directories to constrain the search to.
    explanation : str
        One-sentence explanation of why this invocation is being made.

    Returns
    -------
    str
        Human-readable summary of matching files (limited to MAX_RESULTS).
    """
    # Preparar raíces de búsqueda
    roots = [Path(d).expanduser().resolve() for d in (target_directories or ["."])]

    # Compilar patrón (regExp) a partir de la query literal
    flags = 0 if CASE_SENSITIVE else re.IGNORECASE
    pattern = re.compile(re.escape(query), flags)

    # 1. Recolectar paths candidatos
    all_files = _iter_code_files(roots, tuple(e.lower() for e in DEFAULT_EXTS))

    # 2. Buscar en paralelo
    matches: list[str] = []
    with cf.ThreadPoolExecutor() as pool:
        for path in pool.map(lambda p: _file_contains(pattern, p), all_files):
            if path:
                matches.append(str(path))
                if len(matches) >= MAX_RESULTS:
                    break

    # 3. Formatear salida
    header = (
        f"Search completed for query: '{query}'. "
        f"{explanation or 'Semantic code search triggered.'}\n"
        f"Results: {len(matches)} file(s) matched.\n"
    )
    body = "\n".join(matches)
    return header + (body or "No relevant files found.")

