import os
import ast
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

# Intentamos importar librerías opcionales, si fallan, simplemente no lintaremos esos tipos
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

def _lint_python(content: str) -> str | None:
    try:
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"Python SyntaxError: {e.msg} at line {e.lineno}, column {e.offset}"

def _lint_json(content: str) -> str | None:
    try:
        json.loads(content)
        return None
    except json.JSONDecodeError as e:
        return f"JSON SyntaxError: {e.msg} at line {e.lineno}, column {e.colno}"

def _lint_yaml(content: str) -> str | None:
    if not HAS_YAML:
        return None # No podemos validar si falta la librería
    try:
        yaml.safe_load(content)
        return None
    except yaml.YAMLError as e:
        return f"YAML SyntaxError: {str(e)}"

def _lint_javascript(content: str) -> str | None:
    """
    Valida JS/TS usando 'node --check'.
    Requiere que Node.js esté instalado en el sistema.
    """
    if not shutil.which("node"):
        return None # Node no instalado, omitimos validación silenciosamente

    # Node requiere un archivo físico para --check (a veces stdin falla dependiendo de la versión)
    try:
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode='w', encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Ejecutamos node --check
        result = subprocess.run(
            ["node", "--check", tmp_path],
            capture_output=True,
            text=True,
            timeout=5 # Timeout de seguridad
        )
        
        if result.returncode != 0:
            # Limpiamos la salida para quitar la ruta del archivo temporal y que sea legible
            error_msg = result.stderr.replace(tmp_path, "file.js").strip()
            # Tomamos solo las primeras líneas del error para no saturar al agente
            return f"JavaScript SyntaxError:\n{'\n'.join(error_msg.splitlines()[:5])}"
            
        return None

    except Exception:
        return None # Si falla el subproceso, asumimos válido para no bloquear
    finally:
        # Limpieza del archivo temporal
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

def _lint_bash(content: str) -> str | None:
    """Valida scripts de shell usando 'bash -n'"""
    if not shutil.which("bash"):
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False, mode='w', encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = subprocess.run(
            ["bash", "-n", tmp_path],
            capture_output=True,
            text=True,
            timeout=3
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.replace(tmp_path, "script.sh").strip()
            return f"Bash SyntaxError: {error_msg}"
        return None
    except Exception:
        return None
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

# --- Main Dispatcher ---

def lint_code_check(file_path: str | Path, content: str) -> str | None:
    """
    Función genérica de linting. 
    Retorna un string con el error si la validación falla, o None si pasa.
    """
    path_obj = Path(file_path)
    ext = path_obj.suffix.lower()

    # Mapeo de extensiones a validadores
    if ext == '.py':
        return _lint_python(content)
    
    elif ext == '.json':
        return _lint_json(content)
    
    elif ext in ['.yaml', '.yml']:
        return _lint_yaml(content)
    
    elif ext in ['.js', '.mjs', '.cjs', '.ts', '.tsx']:
        # Nota: node --check funciona decentemente para TS básico también
        return _lint_javascript(content)
    
    elif ext in ['.sh', '.bash']:
        return _lint_bash(content)

    return None