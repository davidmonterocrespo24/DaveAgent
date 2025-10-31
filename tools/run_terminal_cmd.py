import subprocess
from pathlib import Path
import os

# Usar el directorio actual como workspace
WORKSPACE = Path(os.getcwd()).resolve()

async def run_terminal_cmd(command: str, require_user_approval: bool = True,
                          explanation: str = "", timeout: int = 30) -> str:
    """
    Execute a terminal command with USER APPROVAL REQUIRED for safety.

    IMPORTANT: Commands that can modify the system, install packages, delete files,
    or make significant changes MUST have require_user_approval=True (default).

    Args:
        command: The shell command to execute (cmd/powershell on Windows, bash on Linux)
        require_user_approval: If True, returns approval request instead of executing
        explanation: Explanation of what the command does and why it's needed
        timeout: Maximum execution time in seconds

    Returns:
        Command output or approval request message

    Examples:
        - Safe: "ls -la" or "dir"
        - Requires approval: "pip install package", "rm -rf folder", "shutdown"
    """
    # SIEMPRE pedir aprobación para comandos potencialmente peligrosos
    dangerous_keywords = ['rm', 'del', 'format', 'shutdown', 'reboot', 'kill',
                         'pip install', 'npm install', 'apt-get', 'yum', 'curl', 'wget']

    is_dangerous = any(keyword in command.lower() for keyword in dangerous_keywords)

    if require_user_approval or is_dangerous:
        # Mensaje simplificado sin caracteres especiales para compatibilidad con Windows
        approval_msg = f"""
==================================================================
  COMMAND APPROVAL REQUIRED
==================================================================
  Command: {command[:50]}
  Explanation: {explanation or 'No explanation provided'}

  WARNING: This command requires user approval before execution
  for security reasons.

  To execute, user must explicitly confirm.
==================================================================

ACTION REQUIRED: Ask the user if they want to execute this command.
"""
        return approval_msg

    # Ejecutar comando solo si no requiere aprobación
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            cwd=WORKSPACE,
            text=True,
            timeout=timeout
        )

        output = f"Comando ejecutado: {command}\n"
        if result.stdout:
            output += f"\nSalida:\n{result.stdout}"
        if result.stderr:
            output += f"\nErrores/Advertencias:\n{result.stderr}"
        output += f"\nCódigo de retorno: {result.returncode}"

        return output

    except subprocess.TimeoutExpired:
        return f"⏱️ El comando excedió el tiempo límite de {timeout} segundos: {command}"
    except Exception as e:
        return f"❌ Error ejecutando comando: {str(e)}"
    
