"""
CLI Entry point for CodeAgent
Este archivo se ejecuta cuando el usuario escribe 'codeagent' en la terminal
"""
import asyncio
import sys
import os
from pathlib import Path


def main():
    """
    Punto de entrada principal para el comando 'codeagent'
    Se ejecuta cuando el usuario escribe 'codeagent' en cualquier directorio
    """
    # Agregar el directorio raíz del paquete al path
    package_root = Path(__file__).parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    # Importar main desde el directorio raíz
    from main import main as run_codeagent

    # Detectar flags
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    help_mode = "--help" in sys.argv or "-h" in sys.argv
    version_mode = "--version" in sys.argv or "-v" in sys.argv

    # Mostrar ayuda
    if help_mode:
        print_help()
        return 0

    # Mostrar versión
    if version_mode:
        print_version()
        return 0

    # Mostrar información del directorio de trabajo
    working_dir = Path.cwd()
    print(f"🚀 Iniciando CodeAgent en: {working_dir}")
    print(f"📂 Directorio de trabajo: {working_dir.absolute()}\n")

    # Cambiar al directorio de trabajo actual (donde el usuario ejecutó el comando)
    os.chdir(working_dir)

    if debug_mode:
        print("🐛 Modo DEBUG activado\n")

    # Ejecutar CodeAgent
    try:
        asyncio.run(run_codeagent(debug=debug_mode))
        return 0
    except KeyboardInterrupt:
        print("\n\n👋 CodeAgent terminado por el usuario")
        return 0
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1


def print_help():
    """Muestra la ayuda del comando"""
    print("=" * 60)
    print("         CodeAgent CLI - AI Coding Assistant")
    print("=" * 60)
    print()
    print("USAGE:")
    print("    codeagent [OPTIONS]")
    print()
    print("OPTIONS:")
    print("    -h, --help      Muestra esta ayuda")
    print("    -v, --version   Muestra la version")
    print("    -d, --debug     Activa modo debug")
    print()
    print("DESCRIPTION:")
    print("    CodeAgent trabaja en tu directorio actual.")
    print("    Puede crear/editar archivos, buscar codigo,")
    print("    ejecutar Git, trabajar con JSON/CSV, y mas.")
    print()
    print("EXAMPLES:")
    print("    codeagent              # Iniciar normalmente")
    print("    codeagent --debug      # Con logs detallados")
    print()
    print("COMANDOS INTERNOS:")
    print("    /help      - Ayuda")
    print("    /debug     - Toggle debug")
    print("    /logs      - Ver ubicacion de logs")
    print("    /exit      - Salir")
    print()
    print("=" * 60)


def print_version():
    """Muestra la versión de CodeAgent"""
    print("=" * 60)
    print("         CodeAgent CLI v1.0.0")
    print("=" * 60)
    print(f"Python:   {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print()
    print("Built with AutoGen 0.4")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
