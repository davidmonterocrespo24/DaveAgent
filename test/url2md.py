#!/usr/bin/env python3
"""
web_saver_with_markdown.py

Descarga páginas a partir de una URL base y genera árbol de archivos.
Opcionalmente convierte cada página HTML a Markdown usando MarkItDown.
"""

import argparse
import asyncio
import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import aiohttp
from bs4 import BeautifulSoup
from yarl import URL
from tqdm.asyncio import tqdm

# Intentamos importar MarkItDown (opcional)
try:
    from markitdown import MarkItDown
except Exception:
    MarkItDown = None

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("web_saver")


def clean_url(u: str) -> str:
    parsed = urlparse(u)
    clean = parsed._replace(query="", fragment="")
    return urlunparse(clean)


def same_domain(u: str, base_domain: str) -> bool:
    try:
        return urlparse(u).netloc == base_domain
    except Exception:
        return False


def url_to_local_path(base_output: Path, url: str) -> Path:
    """
    Convierte una URL a una ruta local:
      https://example.com/a/b/      -> output/example.com/a/b/index.html
      https://example.com/a/b/c.md -> output/example.com/a/b/c.md   (preserva extensión si existe)
    """
    parsed = urlparse(url)
    path = parsed.path or "/"
    segments = [seg for seg in path.split("/") if seg]

    dom_dir = base_output / parsed.netloc

    if not segments:
        return dom_dir / "index.html"

    last = segments[-1]
    # Determinar si el último segmento parece tener una extensión de archivo conocida
    # Solo considerar extensiones comunes de archivos web
    has_file_extension = "." in last and last.split(".")[-1].lower() in {
        "html", "htm", "md", "txt", "json", "xml", "pdf", "css", "js",
        "jpg", "jpeg", "png", "gif", "svg", "webp", "ico"
    }

    if has_file_extension:
        file_path = dom_dir.joinpath(*segments)
    else:
        file_path = dom_dir.joinpath(*segments, "index.html")

    return file_path


async def fetch_text(session: aiohttp.ClientSession, url: str, timeout=30) -> Tuple[int, str]:
    async with session.get(url, timeout=timeout) as resp:
        text = await resp.text(errors='ignore')
        return resp.status, text


async def fetch_bytes(session: aiohttp.ClientSession, url: str, timeout=30) -> Tuple[int, bytes]:
    async with session.get(url, timeout=timeout) as resp:
        data = await resp.read()
        return resp.status, data


def extract_links(html: str, base_url: str) -> Set[str]:
    soup = BeautifulSoup(html, "html.parser")
    hrefs = set()
    for a in soup.find_all("a", href=True):
        raw = a['href'].strip()
        if raw.startswith("javascript:") or raw.startswith("mailto:"):
            continue
        abs_url = urljoin(base_url, raw)
        clean = clean_url(abs_url)
        hrefs.add(clean)
    return hrefs


def ensure_parent(path: Path):
    """
    Asegura que el directorio padre existe, manejando conflictos en Windows
    donde un archivo puede estar bloqueando la creación de un directorio.
    """
    try:
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
    except (FileExistsError, OSError):
        # Si hay un conflicto, intentar crear rutas intermedias manualmente
        parent = path.parent
        parts = []
        while not parent.exists():
            parts.append(parent)
            parent = parent.parent

        # Crear directorios de arriba hacia abajo
        for p in reversed(parts):
            try:
                # Si existe un archivo con el mismo nombre, lo eliminamos
                if p.exists() and p.is_file():
                    p.unlink()
                p.mkdir(exist_ok=True)
            except (FileExistsError, OSError):
                # Si todavía falla, intentar con una ruta alternativa
                pass


async def download_asset(session: aiohttp.ClientSession, url: str, local_path: Path):
    try:
        status, content = await fetch_bytes(session, url)
        if status == 200:
            ensure_parent(local_path)
            with open(local_path, "wb") as f:
                f.write(content)
            return True
        else:
            logger.debug(f"Asset {url} returned {status}")
            return False
    except Exception as e:
        logger.debug(f"Error downloading asset {url}: {e}")
        return False


def make_relative(from_path: Path, to_path: Path) -> str:
    try:
        return os.path.relpath(to_path, start=from_path.parent).replace(os.sep, "/")
    except Exception:
        return str(to_path)


def html_to_markdown(markitdown_instance, html: str, source_url: str) -> str:
    """
    Convierte HTML a markdown usando MarkItDown. Se crea un tmp file y se borra luego.
    Devuelve el markdown ya con header metadata.
    """
    # crear archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp:
        tmp.write(html)
        tmp_path = tmp.name

    try:
        result = markitdown_instance.convert(tmp_path)
        md = result.text_content
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    metadata_header = f"""---
source_url: {source_url}
imported_date: {datetime.utcnow().isoformat()}Z
---

"""
    return metadata_header + md


async def crawler(
    base_url: str,
    output_dir: Path,
    max_depth: int = 2,
    max_pages: int = 200,
    include_pattern: str = None,
    exclude_pattern: str = None,
    include_images: bool = True,
    css_selector: str = None,
    concurrency: int = 8,
    to_markdown: bool = False,
    markitdown_instance=None,
):
    base_url = clean_url(base_url)
    base_domain = urlparse(base_url).netloc
    logger.info(f"Base: {base_url} (domain {base_domain})")

    include_re = re.compile(include_pattern) if include_pattern else None
    exclude_re = re.compile(exclude_pattern) if exclude_pattern else None

    to_visit = [(base_url, 0)]
    visited: Set[str] = set()
    discovered: Set[str] = set([base_url])
    url_to_local: Dict[str, Path] = {}

    def local_for(u: str) -> Path:
        if u not in url_to_local:
            url_to_local[u] = url_to_local_path(output_dir, u)
        return url_to_local[u]

    session_timeout = aiohttp.ClientTimeout(total=60)
    semaphore = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession(timeout=session_timeout) as session:
        # Phase 1: BFS discover URLs
        logger.info("Descubriendo URLs...")
        while to_visit and len(discovered) < max_pages:
            url, depth = to_visit.pop(0)
            if url in visited:
                continue
            if depth > max_depth:
                continue

            visited.add(url)
            try:
                async with semaphore:
                    status, body = await fetch_text(session, url)
                if status != 200:
                    logger.debug(f"Skipping {url} status {status}")
                    continue

                links = extract_links(body, url)
                for link in links:
                    if not same_domain(link, base_domain):
                        continue
                    if include_re and not include_re.search(link):
                        continue
                    if exclude_re and exclude_re.search(link):
                        continue
                    if link not in discovered and len(discovered) < max_pages:
                        discovered.add(link)
                        to_visit.append((link, depth + 1))

            except Exception as e:
                logger.warning(f"Error discovering {url}: {e}")
                continue

        discovered_list = sorted(discovered)
        logger.info(f"Descubiertos {len(discovered_list)} URLs (limit {max_pages})")

        for u in discovered_list:
            _ = local_for(u)

        # Phase 2: descargar páginas y reescribir assets locales
        logger.info("Descargando y guardando páginas...")
        tasks = []
        for url in discovered_list:
            tasks.append(_process_and_save_page(
                session, semaphore, url, local_for, include_images, css_selector, output_dir, to_markdown, markitdown_instance
            ))
        await asyncio.gather(*tasks)

        # Phase 3: reescribir enlaces entre páginas
        logger.info("Reescribiendo enlaces locales entre páginas...")
        for url in discovered_list:
            src_path = local_for(url)
            if not src_path.exists():
                continue
            try:
                html = src_path.read_text(encoding="utf-8", errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                modified = False
                for a in soup.find_all("a", href=True):
                    raw = a['href'].strip()
                    if raw.startswith("javascript:") or raw.startswith("mailto:"):
                        continue
                    abs_url = clean_url(urljoin(url, raw))
                    if abs_url in url_to_local:
                        target_local = url_to_local[abs_url]
                        rel = make_relative(src_path, target_local)
                        a['href'] = rel
                        modified = True
                if modified:
                    src_path.write_text(str(soup), encoding="utf-8")
            except Exception as e:
                logger.debug(f"Error reescribiendo links en {src_path}: {e}")

    logger.info("Proceso completado. Revisá el directorio de salida.")


async def _process_and_save_page(session, semaphore, url, local_for, include_images, css_selector, output_dir: Path, to_markdown: bool, markitdown_instance):
    async with semaphore:
        try:
            status, html = await fetch_text(session, url)
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return

    if status != 200:
        logger.debug(f"Skip {url} status {status}")
        return

    if css_selector:
        try:
            soup_sel = BeautifulSoup(html, "html.parser")
            sel = soup_sel.select_one(css_selector)
            if sel:
                html = str(sel)
            else:
                logger.debug(f"Selector {css_selector} no encontrado en {url} — guardando página completa")
        except Exception as e:
            logger.debug(f"Error aplicando selector: {e}")

    soup = BeautifulSoup(html, "html.parser")
    assets = []

    if include_images:
        for tag in soup.find_all(["img", "script", "audio", "video"], src=True):
            orig = clean_url(urljoin(url, tag['src']))
            assets.append((tag, 'src', orig))
        for tag in soup.find_all("link", href=True):
            rel = (tag.get("rel") or [])
            if "stylesheet" in rel:
                orig = clean_url(urljoin(url, tag['href']))
                assets.append((tag, 'href', orig))

    asset_tasks = []
    for tag, attr, asset_url in assets:
        parsed = urlparse(asset_url)
        local_asset_path = output_dir / parsed.netloc / "assets" / Path(parsed.path.lstrip("/"))
        if str(local_asset_path).endswith("/"):
            local_asset_path = local_asset_path / "index.bin"
        asset_tasks.append((asset_url, local_asset_path, tag, attr))

    async def _dl_asset(asset_url, local_asset_path, tag, attr):
        try:
            ok = await download_asset(session, asset_url, local_asset_path)
            if ok:
                tag[attr] = os.path.relpath(local_asset_path, start=local_for(url).parent).replace(os.sep, "/")
        except Exception as e:
            logger.debug(f"Error descargando asset {asset_url}: {e}")

    await asyncio.gather(*[_dl_asset(a[0], a[1], a[2], a[3]) for a in asset_tasks])

    # Guardar HTML
    local_path = local_for(url)
    ensure_parent(local_path)
    try:
        local_path.write_text(str(soup), encoding="utf-8")
        logger.info(f"Guardado {url} -> {local_path}")
    except Exception as e:
        logger.warning(f"No pude guardar {local_path}: {e}")

    # Convertir a Markdown si corresponde
    if to_markdown and markitdown_instance:
        try:
            md_text = html_to_markdown(markitdown_instance, str(soup), url)
            md_path = local_path.with_suffix('.md')
            md_path.write_text(md_text, encoding="utf-8")
            logger.info(f"Markdown creado: {md_path}")
        except Exception as e:
            logger.warning(f"Error convirtiendo a markdown {url}: {e}")


def parse_args():
    p = argparse.ArgumentParser(description="Descarga un sitio y opcionalmente convierte HTML a Markdown con MarkItDown.")
    p.add_argument("--base-url", required=True, help="URL inicial")
    p.add_argument("--output", default="./site_dump", help="Directorio de salida")
    p.add_argument("--max-depth", type=int, default=2, help="Profundidad máxima (default 2)")
    p.add_argument("--max-pages", type=int, default=200, help="Máximo de páginas (default 200)")
    p.add_argument("--include", default=None, help="Regex include para URLs")
    p.add_argument("--exclude", default=None, help="Regex exclude para URLs")
    p.add_argument("--include-images", action="store_true", help="Descargar imágenes y assets relacionados")
    p.add_argument("--css-selector", default=None, help="Selector CSS para extraer sólo una parte de la página")
    p.add_argument("--concurrency", type=int, default=8, help="Concurrent requests")
    p.add_argument("--to-markdown", action="store_true", help="Convertir cada HTML a Markdown usando MarkItDown")
    return p.parse_args()


def main():
    args = parse_args()
    if args.to_markdown and MarkItDown is None:
        logger.error("Pediste --to-markdown pero 'markitdown' no está instalado. Ejecuta: pip install markitdown")
        raise SystemExit(1)

    markitdown_instance = MarkItDown() if args.to_markdown else None

    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    asyncio.run(crawler(
        base_url=args.base_url,
        output_dir=output_dir,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        include_pattern=args.include,
        exclude_pattern=args.exclude,
        include_images=args.include_images,
        css_selector=args.css_selector,
        concurrency=args.concurrency,
        to_markdown=args.to_markdown,
        markitdown_instance=markitdown_instance,
    ))


if __name__ == "__main__":
    main()
