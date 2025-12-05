"""
CLI Entry point for DaveAgent
Este archivo se ejecuta cuando el usuario escribe 'daveagent' en la terminal
"""
import asyncio
import sys
import os
import argparse
from pathlib import Path


def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        prog='daveagent',
        description='DaveAgent - AI-powered coding assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Argumentos de configuración
    parser.add_argument(
        '--api-key',
        type=str,
        help='API key para el modelo LLM (o usar DAVEAGENT_API_KEY en .daveagent/.env)'
    )

    parser.add_argument(
        '--base-url',
        type=str,
        default=None,
        help='Base URL de la API (default: https://api.deepseek.com)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Nombre del modelo a usar (default: deepseek-reasoner)'
    )

    parser.add_argument(
        '--no-ssl-verify',
        action='store_true',
        help='Desactiva la verificación de certificados SSL'
    )

    parser.add_argument(
        '--ssl-verify',
        type=str,
        choices=['true', 'false'],
        help='Habilita/deshabilita verificación SSL explícitamente (true/false)'
    )

    # Argumentos de modo
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Activa modo debug con logs detallados'
    )

    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Muestra la versión de DaveAgent'
    )

    return parser.parse_args()


def main():
    """
    Punto de entrada principal para el comando 'daveagent'
    Se ejecuta cuando el usuario escribe 'daveagent' en cualquier directorio
    """
    # Parsear argumentos
    args = parse_arguments()

    # Mostrar versión
    if args.version:
        print_version()
        return 0

    # Agregar el directorio raíz del paquete al path
    package_root = Path(__file__).parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    # Importar main desde src
    from src.main import main as run_daveagent

    # Mostrar información del directorio de trabajo
    working_dir = Path.cwd()
    print(f"🚀 Iniciando DaveAgent en: {working_dir}")
    print(f"📂 Directorio de trabajo: {working_dir.absolute()}\n")

    # Cambiar al directorio de trabajo actual (donde el usuario ejecutó el comando)
    os.chdir(working_dir)

    if args.debug:
        print("🐛 Modo DEBUG activado\n")

    # Ejecutar DaveAgent con configuración
    try:
        # Determinar configuración SSL
        ssl_verify = None
        if args.no_ssl_verify:
            ssl_verify = False
        elif args.ssl_verify:
            ssl_verify = args.ssl_verify.lower() == 'true'

        asyncio.run(run_daveagent(
            debug=args.debug,
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model,
            ssl_verify=ssl_verify
        ))
        return 0
    except KeyboardInterrupt:
        print("\n\n👋 DaveAgent terminado por el usuario")
        return 0
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1


def print_help():
    """Muestra la ayuda del comando (no se usa, argparse lo maneja)"""
    # Esta función ya no es necesaria, argparse maneja --help automáticamente
    pass


def print_version():
    """Muestra la versión de DaveAgent"""
    print("=" * 60)
    print("         DaveAgent CLI v1.0.0")
    print("=" * 60)
    print(f"Python:   {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print()
    print("Built with AutoGen 0.7")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
