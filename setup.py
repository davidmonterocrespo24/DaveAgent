"""
Setup configuration for DaveAgent
"""

from pathlib import Path

from setuptools import find_packages, setup

# Leer el README para la descripción larga
this_directory = Path(__file__).parent
long_description = (
    (this_directory / "README.md").read_text(encoding="utf-8")
    if (this_directory / "README.md").exists()
    else ""
)

setup(
    name="daveagent-cli",
    version="1.0.9",
    author="DaveAgent Team",
    author_email="davidmonterocrespo24@gmail.com",
    description="AI-powered coding assistant with intelligent agent orchestration - search, plan, and code with AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/davidmonterocrespo24/DaveAgent",
    project_urls={
        "Bug Tracker": "https://github.com/davidmonterocrespo24/DaveAgent/issues",
        "Documentation": "https://github.com/davidmonterocrespo24/DaveAgent/wiki",
        "Source Code": "https://github.com/davidmonterocrespo24/DaveAgent",
    },
    packages=find_packages(include=["src", "src.*"]),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        # Core dependencies
        "autogen-agentchat>=0.4.0",
        "autogen-ext[openai]>=0.4.0",
        # CLI and UI
        "prompt-toolkit>=3.0.0",
        "rich>=13.0.0",
        "readchar>=4.0.0",
        # Data processing
        "pandas>=2.0.0",
        # Web tools
        "wikipedia>=1.4.0",
        # Utilities
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "daveagent=src.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai agent coding assistant llm autogen",
)
