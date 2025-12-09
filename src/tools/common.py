import os
from pathlib import Path


def get_workspace():
    """Get current workspace dynamically - respects os.chdir() for evaluations"""
    return Path(os.getcwd()).resolve()
