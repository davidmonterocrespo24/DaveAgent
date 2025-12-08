from pathlib import Path

from src.tools.common import get_workspace


async def list_dir(target_dir: str = ".") -> str:
    """Lists files in a directory"""
    try:
        workspace = get_workspace()
        target = workspace / target_dir if not Path(target_dir).is_absolute() else Path(target_dir)
        result = f"Directory listing for {target}:\n"
        for item in sorted(target.iterdir()):
            if item.is_dir():
                result += f"  [DIR]  {item.name}/\n"
            else:
                result += f"  [FILE] {item.name} ({item.stat().st_size} bytes)\n"
        return result
    except Exception as e:
        return f"Error listing directory: {str(e)}"
