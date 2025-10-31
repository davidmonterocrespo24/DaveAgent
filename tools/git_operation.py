"""
Herramientas de Git para AutoGen - Operaciones básicas de git
"""
import asyncio
import os
from typing import Optional, List, Union


async def git_status(path: Optional[str] = None) -> str:
    """
    Obtiene el estado del repositorio git.

    Args:
        path: Ruta del repositorio (usa directorio actual si no se especifica)

    Returns:
        str: Estado del repositorio en formato legible
    """
    work_dir = path or os.getcwd()

    try:
        # Verificar si es un repositorio git
        proc = await asyncio.create_subprocess_exec(
            'git', 'rev-parse', '--git-dir',
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {work_dir} no es un repositorio git"

        # Obtener status
        proc = await asyncio.create_subprocess_exec(
            'git', 'status', '--porcelain=v1', '-b',
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode('utf-8', errors='replace')
        lines = output.strip().split('\n') if output.strip() else []

        # Parsear información
        branch_line = lines[0] if lines else ""
        branch = branch_line[3:].split('...')[0] if branch_line.startswith('##') else "desconocida"

        # Contar archivos por estado
        staged = sum(1 for line in lines[1:] if line and line[0] in 'MADRC')
        modified = sum(1 for line in lines[1:] if line and line[1] in 'MD')
        untracked = sum(1 for line in lines[1:] if line and line.startswith('??'))

        result = f"""Estado del repositorio Git:
Branch: {branch}
Archivos staged: {staged}
Archivos modificados: {modified}
Archivos sin seguimiento: {untracked}

"""
        if len(lines) > 1:
            result += "Detalles:\n" + '\n'.join(lines[1:])
        else:
            result += "Working tree limpio"

        return result

    except Exception as e:
        return f"ERROR ejecutando git status: {str(e)}"


async def git_add(files: Union[str, List[str]], path: Optional[str] = None) -> str:
    """
    Agrega archivos al área de staging de git.

    Args:
        files: Archivo(s) a agregar (string o lista de strings)
        path: Ruta del repositorio (usa directorio actual si no se especifica)

    Returns:
        str: Resultado de la operación
    """
    work_dir = path or os.getcwd()

    if isinstance(files, str):
        files = [files]

    try:
        proc = await asyncio.create_subprocess_exec(
            'git', 'add', *files,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        return f"✓ Archivos agregados exitosamente: {', '.join(files)}"

    except Exception as e:
        return f"ERROR ejecutando git add: {str(e)}"


async def git_commit(message: str, path: Optional[str] = None) -> str:
    """
    Crea un commit con los cambios staged.

    Args:
        message: Mensaje del commit
        path: Ruta del repositorio (usa directorio actual si no se especifica)

    Returns:
        str: Resultado del commit incluyendo hash
    """
    work_dir = path or os.getcwd()

    try:
        proc = await asyncio.create_subprocess_exec(
            'git', 'commit', '-m', message,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode('utf-8', errors='replace')
        return f"✓ Commit creado exitosamente:\n{output}"

    except Exception as e:
        return f"ERROR ejecutando git commit: {str(e)}"


async def git_push(remote: str = "origin", branch: Optional[str] = None,
                   path: Optional[str] = None) -> str:
    """
    Hace push de commits al repositorio remoto.

    Args:
        remote: Nombre del remoto (default: origin)
        branch: Nombre del branch (usa el actual si no se especifica)
        path: Ruta del repositorio (usa directorio actual si no se especifica)

    Returns:
        str: Resultado del push
    """
    work_dir = path or os.getcwd()

    try:
        command = ['git', 'push', remote]
        if branch:
            command.append(branch)

        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        # Git push escribe información en stderr incluso cuando es exitoso
        output = stderr.decode('utf-8', errors='replace') + stdout.decode('utf-8', errors='replace')

        if proc.returncode != 0:
            return f"ERROR en git push:\n{output}"

        return f"✓ Push exitoso:\n{output}"

    except Exception as e:
        return f"ERROR ejecutando git push: {str(e)}"


async def git_pull(remote: str = "origin", branch: Optional[str] = None,
                   path: Optional[str] = None) -> str:
    """
    Hace pull de cambios desde el repositorio remoto.

    Args:
        remote: Nombre del remoto (default: origin)
        branch: Nombre del branch (usa el actual si no se especifica)
        path: Ruta del repositorio (usa directorio actual si no se especifica)

    Returns:
        str: Resultado del pull
    """
    work_dir = path or os.getcwd()

    try:
        command = ['git', 'pull', remote]
        if branch:
            command.append(branch)

        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        output = stdout.decode('utf-8', errors='replace') + stderr.decode('utf-8', errors='replace')

        if proc.returncode != 0:
            return f"ERROR en git pull:\n{output}"

        return f"✓ Pull exitoso:\n{output}"

    except Exception as e:
        return f"ERROR ejecutando git pull: {str(e)}"


async def git_log(limit: int = 10, path: Optional[str] = None) -> str:
    """
    Muestra el historial de commits.

    Args:
        limit: Número máximo de commits a mostrar
        path: Ruta del repositorio (usa directorio actual si no se especifica)

    Returns:
        str: Lista de commits recientes
    """
    work_dir = path or os.getcwd()

    try:
        proc = await asyncio.create_subprocess_exec(
            'git', 'log', f'-{limit}', '--oneline', '--decorate',
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode('utf-8', errors='replace')
        return f"Últimos {limit} commits:\n{output}"

    except Exception as e:
        return f"ERROR ejecutando git log: {str(e)}"


async def git_branch(operation: str = "list", branch_name: Optional[str] = None,
                     path: Optional[str] = None) -> str:
    """
    Gestiona branches de git.

    Args:
        operation: Operación a realizar ('list', 'create', 'delete', 'switch')
        branch_name: Nombre del branch (requerido para create, delete, switch)
        path: Ruta del repositorio (usa directorio actual si no se especifica)

    Returns:
        str: Resultado de la operación
    """
    work_dir = path or os.getcwd()

    try:
        if operation == "list":
            command = ['git', 'branch', '-a']
        elif operation == "create" and branch_name:
            command = ['git', 'branch', branch_name]
        elif operation == "delete" and branch_name:
            command = ['git', 'branch', '-d', branch_name]
        elif operation == "switch" and branch_name:
            command = ['git', 'checkout', branch_name]
        else:
            return f"ERROR: Operación '{operation}' inválida o falta branch_name"

        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode('utf-8', errors='replace')
        return output if output else f"✓ Operación '{operation}' completada"

    except Exception as e:
        return f"ERROR ejecutando git branch: {str(e)}"


async def git_diff(cached: bool = False, path: Optional[str] = None) -> str:
    """
    Muestra las diferencias en el repositorio.

    Args:
        cached: Si True, muestra diff de cambios staged
        path: Ruta del repositorio (usa directorio actual si no se especifica)

    Returns:
        str: Diff de los cambios
    """
    work_dir = path or os.getcwd()

    try:
        command = ['git', 'diff']
        if cached:
            command.append('--cached')

        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"ERROR: {stderr.decode('utf-8', errors='replace')}"

        output = stdout.decode('utf-8', errors='replace')
        if not output:
            return "No hay cambios para mostrar"

        return f"Diferencias {'(staged)' if cached else '(working tree)'}:\n{output}"

    except Exception as e:
        return f"ERROR ejecutando git diff: {str(e)}"
