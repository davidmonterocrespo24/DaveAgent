"""
CLI Entry point for DaveAgent
Este archivo se ejecuta cuando el usuario escribe 'daveagent' en la terminal
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path


def parse_arguments():
    """Parses command line arguments"""
    parser = argparse.ArgumentParser(
        prog="daveagent",
        description="DaveAgent - AI-powered coding assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Configuration arguments
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for LLM model (or use DAVEAGENT_API_KEY in .daveagent/.env)",
    )

    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="API base URL (default: https://api.deepseek.com)",
    )

    parser.add_argument(
        "--model", type=str, default=None, help="Model name to use (default: deepseek-reasoner)"
    )

    parser.add_argument(
        "--no-ssl-verify", action="store_true", help="Disables SSL certificate verification"
    )

    parser.add_argument(
        "--ssl-verify",
        type=str,
        choices=["true", "false"],
        help="Explicitly enables/disables SSL verification (true/false)",
    )

    # Mode arguments
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enables debug mode with detailed logs"
    )

    parser.add_argument("-v", "--version", action="store_true", help="Shows DaveAgent version")

    return parser.parse_args()


def main():
    """
    Main entry point for the 'daveagent' command
    Executes when the user types 'daveagent' in any directory
    """
    # Parse arguments
    args = parse_arguments()

    # Show version
    if args.version:
        print_version()
        return 0

    # Add package root directory to path
    package_root = Path(__file__).parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    # Import main from src
    from src.main import main as run_daveagent

    # Show working directory information
    working_dir = Path.cwd()    
    # Change to current working directory (where user executed the command)
    os.chdir(working_dir)

    if args.debug:
        print("🐛 DEBUG mode enabled\n")

    # Execute DaveAgent with configuration
    try:
        # Determine SSL configuration
        ssl_verify = None
        if args.no_ssl_verify:
            ssl_verify = False
        elif args.ssl_verify:
            ssl_verify = args.ssl_verify.lower() == "true"

        asyncio.run(
            run_daveagent(
                debug=args.debug,
                api_key=args.api_key,
                base_url=args.base_url,
                model=args.model,
                ssl_verify=ssl_verify,
            )
        )
        return 0
    except KeyboardInterrupt:
        print("\n\n👋 DaveAgent terminated by user")
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return 1


def print_help():
    """Shows command help (not used, argparse handles it)"""
    # This function is no longer needed, argparse handles --help automatically
    pass


def print_version():
    """Shows DaveAgent version"""
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
