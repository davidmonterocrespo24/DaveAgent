"""
Basic tests to verify project setup
"""
import pytest


def test_import_main():
    """Test that main module can be imported"""
    from src import main
    assert main is not None


def test_import_config():
    """Test that config module can be imported"""
    from src import config
    assert config is not None


def test_version():
    """Test that version is defined"""
    from src import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_tools_import():
    """Test that tools can be imported"""
    from src.tools import edit_file, read_file, write_file
    assert read_file is not None
    assert write_file is not None
    assert edit_file is not None


def test_agents_import():
    """Test that agents can be imported"""
    from src.agents import CodeSearcher
    assert CodeSearcher is not None
